"""
FastAPI application entrypoint.

Responsibilities:
- Define endpoints for health, compute, and static serving.
- Wire Pydantic models for request/response.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path

import config
import momentum


class ComputeRequest(BaseModel):
    """Request body for momentum computation."""

    tickers: List[str] = Field(..., max_items=3, min_items=1)
    unit: Literal["month", "week", "day"]
    n: int = Field(..., ge=1)
    as_of_period: str  # YYYY-MM for month, YYYY-MM-DD for week/day


class ComputeResponse(BaseModel):
    """Response payload for momentum computation."""

    results: List[Optional[float]]
    summary: Dict[str, Any]
    anchors: Dict[str, str]


app = FastAPI(title="Dual Momentum Calculator MVP", version="1.0.0")

# Serve static files from the directory next to this file
_BASE_DIR = Path(__file__).parent
_STATIC_DIR = _BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
async def read_index() -> FileResponse:
    """Serve the frontend index.html at root."""

    return FileResponse(str(_STATIC_DIR / "index.html"))


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""

    return {"status": "healthy", "api_base": config.STOCK_API_BASE}


@app.post("/compute", response_model=ComputeResponse)
async def compute_momentum(request: ComputeRequest) -> ComputeResponse:
    """Compute momentum values and return them with anchors and summary."""

    try:
        results, anchors = momentum.calculate(
            tickers=request.tickers,
            unit=request.unit,
            n=request.n,
            as_of_period=request.as_of_period,
        )
        return ComputeResponse(
            results=results,
            summary={
                "tickers": request.tickers,
                "unit": request.unit,
                "n": request.n,
                "as_of_period": request.as_of_period,
            },
            anchors=anchors,
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))
