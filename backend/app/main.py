"""
Career Trajectory Simulator — FastAPI Application Entry Point

This module creates the FastAPI application instance, registers middleware,
mounts API routers, and exposes health-check endpoints.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.db.health import check_db_connection

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="Career Trajectory Simulator API",
        description=(
            "Simulate possible career paths from your current role, "
            "identify skill gaps, and generate practical roadmaps."
        ),
        version="0.2.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            *settings.CORS_ORIGINS,
            "https://career-trajectory-simulator-frontend.onrender.com",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(StarletteHTTPException)
    async def structured_http_error_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, str):
            message = detail
        elif isinstance(detail, dict):
            message = detail.get("message", "The request could not be completed.")
        else:
            message = "The request could not be completed."
        code = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
        }.get(exc.status_code, "HTTP_ERROR")
        details = (
            {key: value for key, value in detail.items() if key not in {"code", "message"}}
            if isinstance(detail, dict)
            else None
        )
        if isinstance(detail, dict) and isinstance(detail.get("code"), str):
            code = detail["code"]
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details,
                }
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": [
                        {
                            "location": list(error["loc"]),
                            "message": error["msg"],
                            "type": error["type"],
                        }
                        for error in exc.errors()
                    ],
                }
            },
        )

    # ── API routers ──────────────────────────────────────────────────────
    from app.api.v1.routes import auth, catalog, history, profiles, roadmap, simulation
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(catalog.router, prefix="/api/v1", tags=["Catalog"])
    app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Profiles"])
    app.include_router(simulation.router, prefix="/api/v1/simulate", tags=["Simulation"])
    app.include_router(roadmap.router, prefix="/api/v1/roadmap", tags=["Roadmap"])
    app.include_router(history.router, prefix="/api/v1/history", tags=["History"])

    return app


app = create_app()


# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Combined liveness + DB readiness probe.

    Returns HTTP 200 always (so load-balancers don't kill the pod).
    The db.status field reports the actual DB connectivity state.
    """
    db_status = await check_db_connection()
    return {
        "status": "ok",
        "service": "career-trajectory-simulator",
        "version": "0.2.0",
        "db": db_status,
    }
