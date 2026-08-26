from fastapi import FastAPI

from app.admin.auth.router import router as admin_auth_router
from app.admin.bookings.router import router as admin_bookings_router
from app.admin.csv.router import router as admin_csv_router
from app.admin.metadata.router import router as admin_metadata_router
from app.shared.errors import register_error_handlers
from app.shared.logging import configure_logging
from app.webhook.webhook_router import router as webhook_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="WhatsApp Meeting Assistant Backend")
    register_error_handlers(app)

    app.include_router(admin_auth_router)
    app.include_router(admin_bookings_router)
    app.include_router(admin_metadata_router)
    app.include_router(admin_csv_router)
    app.include_router(webhook_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
