from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ToneLiteral = Literal["friendly", "neutral", "formal", "bold"]
PriorityLiteral = Literal["P0", "P1", "P2"]


class CharCount(BaseModel):
    headline: int = Field(ge=0)
    body: int = Field(ge=0)


class RiskFlag(BaseModel):
    type: str
    note: str
    suggest_fix: str


class CopyVariant(BaseModel):
    headline: str
    body: str
    cta: str
    rationale: str
    char_count: CharCount
    risk_flags: list[RiskFlag] = Field(default_factory=list)

    @model_validator(mode="after")
    def sync_char_count(self) -> "CopyVariant":
        # Normalizes counters so downstream export/UI always gets trusted values.
        self.char_count = CharCount(headline=len(self.headline), body=len(self.body))
        return self


class SegmentOutput(BaseModel):
    segment_id: str
    segment_name: str
    core_insight: str
    trigger: str
    angle: str
    copies: list[CopyVariant]
    differences_note: str


class QuestionItem(BaseModel):
    q: str
    why: str
    priority: PriorityLiteral


class GlobalRiskItem(BaseModel):
    risk: str
    impact: str
    mitigation: str


class ExportHints(BaseModel):
    how_to_use: list[str]
    ab_test_suggestions: list[str]


class ExecSummary(BaseModel):
    for_marketer: str
    for_non_tech_manager: str


class InputEcho(BaseModel):
    base_text: str
    tone: ToneLiteral
    format_id: str
    variants_per_segment: int = Field(ge=1, le=3)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class SegCraftResponse(BaseModel):
    version: str = Field(pattern=r"^\d+\.\d+$")
    input_echo: InputEcho
    questions: list[QuestionItem] = Field(default_factory=list)
    segments: list[SegmentOutput]
    global_risks: list[GlobalRiskItem] = Field(default_factory=list)
    export_hints: ExportHints
    exec_summary: ExecSummary

    @model_validator(mode="after")
    def validate_lengths(self) -> "SegCraftResponse":
        expected = self.input_echo.variants_per_segment
        for segment in self.segments:
            if len(segment.copies) != expected:
                raise ValueError(
                    "copies.length должна совпадать с variants_per_segment "
                    f"({expected}) для segment_id={segment.segment_id}"
                )
        return self
