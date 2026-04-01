from __future__ import annotations

from pydantic import BaseModel, Field


class KeywordsRequest(BaseModel):
    seed: str = Field(..., min_length=2, max_length=120)
    platform: str = Field(default="tpt")
    gold_only: bool = Field(default=False)
    store_level: str = Field(default="new_store")
    winnable_only: bool = Field(default=True)


class KeywordResult(BaseModel):
    phrase: str
    demand_label: str
    demand_score: int
    opportunity_score: int
    source_hits: list[str]
    tpt_supply_count: int | None
    avg_top5_reviews: float | None
    lowest_page1_reviews: int | None
    winnable_now: bool
    verdict: str
    recommendation_label: str
    recommendation_reason: str
    next_steps: list[str]


class KeywordsResponse(BaseModel):
    platform: str
    seed: str
    items: list[KeywordResult]


class GenerateListingRequest(BaseModel):
    platform: str = Field(default="tpt", pattern="^(tpt|etsy|gumroad)$")
    niche: str = Field(..., min_length=2, max_length=60)
    buyer_type: str = Field(..., min_length=2, max_length=80)
    product_description: str = Field(..., min_length=20, max_length=4000)
    product_stage: str = Field(default="Product is finished", min_length=2, max_length=120)
    seller_confidence: str = Field(
        default="Beginner - I need step-by-step help",
        min_length=2,
        max_length=120,
    )


class GenerateListingResponse(BaseModel):
    title: str
    title_chars: int
    title_limit: int
    tags: list[str]
    tags_count: int
    tags_limit: int
    description_opener: str
    description_snippet: str
    full_description: str
    keyword_angles: list[str]
    gap_opportunities: list[str]


class AuditListingRequest(BaseModel):
    platform: str = Field(default="tpt", pattern="^(tpt|etsy|gumroad)$")
    title: str = Field(..., min_length=5, max_length=200)
    tags: list[str] = Field(default_factory=list)
    description: str = Field(..., min_length=20, max_length=6000)


class AuditListingResponse(BaseModel):
    score_total: int
    title_score: int
    description_score: int
    tags_score: int
    seo_coverage_score: int
    suggested_title: str
    suggested_title_reason: str
    top_fixes: list[str]
