from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .keyword_service import find_keywords
from .listing_service import audit_listing, generate_listing
from .reverse_intel_service import reverse_seller_intel
from .models import (
    AuditListingRequest,
    AuditListingResponse,
    GenerateListingRequest,
    GenerateListingResponse,
    KeywordsRequest,
    KeywordsResponse,
    ReverseIntelRequest,
    ReverseIntelResponse,
)
from .settings import settings

app = FastAPI(title="ListingLift API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/keywords", response_model=KeywordsResponse)
async def keywords_endpoint(payload: KeywordsRequest) -> KeywordsResponse:
    if payload.platform.lower() != "tpt":
        raise HTTPException(status_code=400, detail="MVP currently supports TPT only.")

    try:
        items = await find_keywords(
            seed=payload.seed,
            gold_only=payload.gold_only,
            store_level=payload.store_level,
            winnable_only=payload.winnable_only,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Keyword lookup failed: {exc}") from exc

    return KeywordsResponse(platform="tpt", seed=payload.seed, items=items)


@app.post("/api/generate-listing", response_model=GenerateListingResponse)
def generate_listing_endpoint(payload: GenerateListingRequest) -> GenerateListingResponse:
    try:
        return generate_listing(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Listing generation failed: {exc}") from exc


@app.post("/api/audit", response_model=AuditListingResponse)
def audit_listing_endpoint(payload: AuditListingRequest) -> AuditListingResponse:
    try:
        return audit_listing(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Listing audit failed: {exc}") from exc


@app.post("/api/reverse-intel", response_model=ReverseIntelResponse)
async def reverse_intel_endpoint(payload: ReverseIntelRequest) -> ReverseIntelResponse:
    try:
        return await reverse_seller_intel(keyword=payload.keyword, limit=payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Reverse intel failed: {exc}") from exc
