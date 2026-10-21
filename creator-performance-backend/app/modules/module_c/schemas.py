from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["cooking", "education", "gaming"]
TitleLanguage = Literal["en", "si", "ta", "mixed", "unknown"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Finding(StrictModel):
    id: str
    metric: str
    observed: float | int | None = None
    percentile: float | None = None
    reference_count: int = 0
    statement: str
    basis: Literal["measurement", "category_comparison", "heuristic"]


class Recommendation(StrictModel):
    id: str
    priority: int
    action: str
    how_to_test: str
    evidence_ids: list[str]
    explanation: str


class HistoricalComparison(StrictModel):
    video_id: str
    source_url: str
    visual_similarity: float
    relative_view_performance: float
    outcome: Literal["above_neighbor_baseline", "at_or_below_neighbor_baseline"]
    thumbnail_preview: str | None = None


class WriterStatus(StrictModel):
    provider: str = "rules"
    status: str = "available"
    reason: str | None = None
    model: str | None = None


class Report(StrictModel):
    module: str = "C_thumbnail_expert"
    version: str = "0.1.0"
    category: Category
    report_language: str = "en"
    title_language: TitleLanguage
    measurements: dict[str, float | int | None]
    title_features: dict[str, int]
    capabilities: dict[str, str]
    findings: list[Finding]
    recommendations: list[Recommendation]
    historical_comparisons: list[HistoricalComparison] = Field(default_factory=list)
    image_title_alignment: float | None = None
    mobile_preview: str
    predicted_ctr: None = None
    relative_performance_prediction: None = None
    provenance: dict[str, str | int | None]
    wording: WriterStatus = Field(default_factory=WriterStatus)
    limitations: list[str]


class Rewrite(StrictModel):
    recommendation_id: str
    evidence_ids: list[str]
    explanation: str = Field(min_length=10, max_length=500)


class RewriteResponse(StrictModel):
    recommendations: list[Rewrite] = Field(min_length=1, max_length=6)
