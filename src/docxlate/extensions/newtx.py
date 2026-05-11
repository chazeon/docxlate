from __future__ import annotations

import re

_USEPACKAGE_RE = re.compile(
    r"\\usepackage(?:\s*\[[^\]]*\])?\s*\{(?P<pkgs>[^}]*)\}"
)


def _source_uses_package(tex_source: str, package_name: str) -> bool:
    for match in _USEPACKAGE_RE.finditer(tex_source):
        raw = match.group("pkgs")
        pkgs = [pkg.strip() for pkg in raw.split(",") if pkg.strip()]
        if package_name in pkgs:
            return True
    return False


def register(latex):
    def _newtx_skip_policy(
        tex_source: str,
        configured_skip_packages: set[str],
        _parse_error: Exception | None = None,
    ) -> set[str]:
        if "newtx" in configured_skip_packages:
            return set()
        if _source_uses_package(tex_source, "newtx"):
            # plasTeX can spend excessive time loading TeX-level newtx/fontaxes;
            # these affect typography, not document semantics for DOCX conversion.
            return {"newtx", "fontaxes"}
        return set()

    latex.register_parse_skip_policy(
        initial=_newtx_skip_policy,
        retry=_newtx_skip_policy,
    )
    return None


__all__ = ["register"]
