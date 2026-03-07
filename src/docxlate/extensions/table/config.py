from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TableHeaderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_row_bold: bool | None = None


class TableConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    style_candidates: list[str] | None = None
    fallback_style: str | None = None
    autofit: bool | None = None
    header: TableHeaderConfig | None = None


__all__ = ["TableConfig", "TableHeaderConfig"]
