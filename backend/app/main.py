from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import PROJECT_DIR, get_settings
from app.core.database import SessionLocal, init_database
from app.core.migrations import record_migrations
from app.scheduler.alerts import run_alert_rules
from app.scheduler.jobs import start_scheduler, stop_scheduler
from app.services.seed import seed_estado_zero


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):  # type: ignore[no-untyped-def]
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404 or "." in Path(path).name:
                raise
            return await super().get_response("index.html", scope)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_database()
    with SessionLocal() as db:
        record_migrations(db)
        seed_estado_zero(db)
        run_alert_rules(db)
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Oráculo API",
        version="0.1.0",
        description="Sistema Operacional Estratégico Pessoal local-first.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)

    frontend_dist = PROJECT_DIR / "frontend" / "dist"
    if frontend_dist.is_dir() and (frontend_dist / "index.html").is_file():
        app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="frontend")
    else:
        @app.get("/", include_in_schema=False)
        def root():
            return JSONResponse(
                {
                    "service": "Oráculo",
                    "status": "backend_ready",
                    "today": f"{settings.api_prefix}/today",
                    "docs": "/docs",
                    "frontend": "Execute o build do frontend para servir o cockpit neste mesmo processo.",
                }
            )
    return app


app = create_app()
