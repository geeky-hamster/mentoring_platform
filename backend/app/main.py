"""Mentoring platform API - FastAPI application factory (contract: api-spec.yaml, /api/v1)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.extensions import SessionLocal
from app.core.errors import register_handlers


def build_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        from app.jobs.runner import runner as job_runner
        if config.cfg.JOBS_ENABLED:
            job_runner.start()
        yield
        if config.cfg.JOBS_ENABLED:
            await job_runner.stop()

    app = FastAPI(title="Student Mentoring and Career Support Platform API",
                  version="1.0.0", root_path="",
                  servers=[{"url": "/api/v1"}],
                  lifespan=lifespan)
    app.logger = logging.getLogger("mentoring")

    origins = [o.strip() for o in config.cfg.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Retry-After", "x-request-id"],
    )

    from app.routers import admin, auth, catalogues, dashboards, mentorships, mentors, profiles, requests, sessions

    # Open one session per request. The commit itself lives in TransactionRoute
    # (app/core/transactions.py) so the data is durable BEFORE the response bytes are
    # sent; FastAPI runs dependency exit code after the response is sent, and a plain
    # HTTP middleware commits only after the route response has already started.
    # This middleware only guarantees rollback on error/exception and cleanup.
    @app.middleware("http")
    async def db_session(request, call_next):
        session = SessionLocal()
        request.state.db = session
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                session.rollback()
            return response
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # order matters: profiles registers the literal /mentors/me/profile before mentors' /{mentor_id}
    api = APIRouter(prefix="/api/v1")
    api.include_router(auth.router)
    api.include_router(auth.users_router)
    api.include_router(catalogues.router)
    api.include_router(profiles.router)
    api.include_router(mentorships.router)
    api.include_router(sessions.router)
    api.include_router(requests.router)
    api.include_router(dashboards.router)
    api.include_router(admin.router)
    api.include_router(mentors.availability_router)     # /mentors/me/availability (literal paths first)
    api.include_router(mentors.router)  # last: contains the catch-all /mentors/{mentor_id}
    app.include_router(api)

    register_handlers(app)

    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}

    return app


app = build_app()
