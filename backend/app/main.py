from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api.router import api_router
from app.core.logging import setup_logging, logger
from app.core.exceptions import NirnayPayException
from app.database.init_db import init_db

setup_logging()

app = FastAPI(
    title="Nirnay Pay (RecoveryOS) API",
    version="1.0.0",
    description="Authoritative Revenue Recovery & Decision Backend API for Nirnay Pay",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Database initialization
@app.on_event("startup")
def on_startup():
    try:
        init_db()
        logger.info("Database schemas and merchant seeds initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database schemas on startup: {str(e)}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NirnayPayException)
async def nirnay_pay_exception_handler(request: Request, exc: NirnayPayException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request schema or parameters.",
                "details": {"errors": exc.errors()}
            }
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled internal exception on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected internal server error occurred.",
                "details": {}
            }
        }
    )

app.include_router(api_router)
