from __future__ import annotations

from lxml import etree


class NumberingBackend:
    """Facade for list-numbering operations over a python-docx document."""

    def resolve_list_num_id(self, paragraph, list_type: str, level: int) -> int | None:
        raise NotImplementedError

    def apply_list_numbering(self, paragraph, list_type: str, level: int) -> None:
        raise NotImplementedError

    def cleanup_list_gaps(self, doc) -> None:
        raise NotImplementedError


class DocxOxmlNumberingBackend(NumberingBackend):
    """Current implementation backed by numbering.xml inspection and OXML writes."""

    def _list_style_name(self, list_type: str, level: int) -> str:
        level = max(1, level)
        if list_type == "enumerate":
            if level == 1:
                return "List Number"
            return f"List Number {level}"
        if level == 1:
            return "List Bullet"
        return f"List Bullet {level}"

    def resolve_list_num_id(self, paragraph, list_type: str, level: int) -> int | None:
        root = etree.fromstring(paragraph.part.numbering_part.blob)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

        target_style = self._list_style_name(list_type, level).replace(" ", "")
        target_fmt = "decimal" if list_type == "enumerate" else "bullet"
        target_ilvl = str(max(level - 1, 0))

        abstract_levels: dict[str, dict[str, dict[str, str]]] = {}
        for abstract in root.xpath(".//w:abstractNum", namespaces=ns):
            abstract_id = abstract.get(f"{{{ns['w']}}}abstractNumId")
            level_map: dict[str, dict[str, str]] = {}
            for lvl in abstract.xpath("./w:lvl", namespaces=ns):
                ilvl = lvl.get(f"{{{ns['w']}}}ilvl", "0")
                pstyle = lvl.xpath("string(w:pStyle/@w:val)", namespaces=ns)
                num_fmt = lvl.xpath("string(w:numFmt/@w:val)", namespaces=ns)
                lvl_text = lvl.xpath("string(w:lvlText/@w:val)", namespaces=ns)
                level_map[ilvl] = {
                    "pstyle": pstyle,
                    "num_fmt": num_fmt,
                    "lvl_text": lvl_text,
                }
            abstract_levels[abstract_id] = level_map

        num_to_abs: list[tuple[str, str]] = []
        for num in root.xpath(".//w:num", namespaces=ns):
            num_id = num.get(f"{{{ns['w']}}}numId")
            abs_id = num.xpath("string(w:abstractNumId/@w:val)", namespaces=ns)
            if num_id and abs_id:
                num_to_abs.append((num_id, abs_id))

        # Prefer abstractNum definitions whose level style matches requested list style.
        for num_id, abs_id in num_to_abs:
            level_info = abstract_levels.get(abs_id, {}).get(target_ilvl, {})
            pstyle = level_info.get("pstyle", "")
            if pstyle and pstyle == target_style:
                return int(num_id)

        # Fallback by list format (bullet/decimal), preferring visible bullets.
        for num_id, abs_id in num_to_abs:
            level_info = abstract_levels.get(abs_id, {}).get(target_ilvl, {})
            num_fmt = level_info.get("num_fmt", "")
            lvl_text = level_info.get("lvl_text", "")
            if num_fmt == target_fmt and (
                list_type != "itemize" or (lvl_text and lvl_text.strip())
            ):
                return int(num_id)

        # Last resort by list format (accept invisible bullet definitions too).
        for num_id, abs_id in num_to_abs:
            level_info = abstract_levels.get(abs_id, {}).get(target_ilvl, {})
            num_fmt = level_info.get("num_fmt", "")
            if num_fmt == target_fmt:
                return int(num_id)
        return None

    def apply_list_numbering(self, paragraph, list_type: str, level: int) -> None:
        num_id = self.resolve_list_num_id(paragraph, list_type, level)
        if num_id is None:
            return
        p_pr = paragraph._p.get_or_add_pPr()
        num_pr = p_pr.get_or_add_numPr()
        ilvl = num_pr.get_or_add_ilvl()
        ilvl.val = max(level - 1, 0)
        num_id_elm = num_pr.get_or_add_numId()
        num_id_elm.val = num_id

    def _is_empty_paragraph(self, paragraph) -> bool:
        xml = paragraph._element.xml
        return (
            "<w:pPr" not in xml
            and "<w:r" not in xml
            and "<w:hyperlink" not in xml
            and "<w:bookmarkStart" not in xml
            and "<m:oMath" not in xml
            and "<w:drawing" not in xml
        )

    def _has_numbering(self, paragraph) -> bool:
        return "<w:numPr" in paragraph._element.xml

    def cleanup_list_gaps(self, doc) -> None:
        body = doc._element.body
        paragraphs = list(doc.paragraphs)
        to_remove = []
        for idx, paragraph in enumerate(paragraphs):
            if not self._is_empty_paragraph(paragraph):
                continue
            if idx == 0 or idx + 1 >= len(paragraphs):
                continue
            if self._has_numbering(paragraphs[idx - 1]) and self._has_numbering(
                paragraphs[idx + 1]
            ):
                to_remove.append(paragraph._p)
        for p in to_remove:
            body.remove(p)
