"""API package for Golf Modeling Suite."""

# Sub-modules are imported directly at call-sites to avoid eager loading of
# optional heavy dependencies (alembic, FastAPI routers, etc.) at package
# import time.  Only add an export here after verifying all symbols actually
# exist in the relevant sub-module.

__all__: list[str] = []
