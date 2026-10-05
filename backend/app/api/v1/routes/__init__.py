"""
API Routes
"""
from app.api.v1.routes import auth, catalog, history, profiles, roadmap, simulation

__all__ = ["auth", "catalog", "profiles", "simulation", "roadmap", "history"]
