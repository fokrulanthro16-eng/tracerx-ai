"""
TraceRx AI - API v1 Router Aggregator
"""

from fastapi import APIRouter
from backend.app.api.v1.scan import router as scan_router
from backend.app.api.v1.batches import router as batches_router
from backend.app.api.v1.epcis import router as epcis_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(scan_router)
api_v1_router.include_router(batches_router)
api_v1_router.include_router(epcis_router)
