from fastapi import FastAPI

from app.api.routers import email_router, health_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Mail Microservice",
        description="Microservicio de envío de correos para Turismo Platform",
        version="1.0.0",
    )

    application.include_router(health_router.router)
    application.include_router(email_router.router)

    return application


app = create_app()
