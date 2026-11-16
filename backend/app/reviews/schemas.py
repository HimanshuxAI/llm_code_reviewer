from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    source_code: str = Field(min_length=1, max_length=50_000)
    filename: str | None = Field(default=None, max_length=255)


class FindingOut(BaseModel):
    rule_id: str
    title: str
    severity: str
    line: int
    explanation: str
    suggestion: str
    source: str
    fixed_snippet: str | None


class ReviewOut(BaseModel):
    id: int
    language: str
    score: int
    findings: list[FindingOut]
    created_at: datetime


class ReviewDetail(ReviewOut):
    """Single-review view. Includes the submitted source so the client can
    render it in the editor pane alongside the findings."""

    source_code: str


class ReviewSummary(BaseModel):
    id: int
    language: str
    score: int
    created_at: datetime
