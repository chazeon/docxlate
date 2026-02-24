from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BibliographyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    template: str | None = None
    numbering: Literal["bracket", "none"] | None = None
    indent_in: float | None = Field(default=None, gt=0)
    et_al_limit: int | None = Field(default=None, gt=0)
    macro_replacements: dict[str, str] | None = None
    citation_compress_ranges: bool | None = None
    citation_range_min_run: int | None = Field(default=None, gt=1)


__all__ = ["BibliographyConfig"]
