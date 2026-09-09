"""
TraceRx AI Enterprise Application Entry Point
Re-exports FastAPI application instance from backend.main for modular access.
"""

from backend.main import app

__all__ = ["app"]
