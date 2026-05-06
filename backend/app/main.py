import uuid
import warnings
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Suppress passlib/bcrypt version detection warning (passlib + bcrypt>=4.1 compat)
warnings.filterwarnings("ignore", message=".*trapped.*error reading bcrypt version.*")
warnings.filterwarnings("ignore", message=".*bcrypt.*__about__.*")

from app.config import get_settings
from app.routers import auth, memory, chat, consent, fhir, admin, hospital, legal, opd, ipd, nurse, ward_bot, scheme, insurance, mlc, prescription, notifications, activity_log, patient, profile, screening, documents

logger = structlog.get_logger()


async def _check_services() -> dict:
    """Verify all downstream services are reachable on startup."""
    status = {"mongodb": False, "neo4j": False, "qdrant": False}
    settings = get_settings()

    # MongoDB
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=3000)
        await client[settings.mongodb_db].command("ping")
        status["mongodb"] = True
        logger.info("mongodb_healthy")
    except Exception as e:
        logger.error("mongodb_unhealthy", error=str(e))

    # Neo4j
    try:
        from neo4j import AsyncGraphDatabase
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with driver.session() as session:
            await session.run("RETURN 1")
        await driver.close()
        status["neo4j"] = True
        logger.info("neo4j_healthy")
    except Exception as e:
        logger.error("neo4j_unhealthy", error=str(e))

    # Qdrant
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        client.get_collections()
        status["qdrant"] = True
        logger.info("qdrant_healthy")
    except Exception as e:
        logger.error("qdrant_unhealthy", error=str(e))

    return status


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("medgraph_starting")
    service_status = await _check_services()
    app.state.service_status = service_status
    all_healthy = all(service_status.values())
    if all_healthy:
        logger.info("all_services_healthy")
    else:
        logger.warning("some_services_unhealthy", status=service_status)
    yield
    logger.info("medgraph_shutting_down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="MedGraph AI",
        version="1.0.0",
        description="Healthcare Interoperability Platform — Cognizant Technoverse 2026",
        lifespan=lifespan,
    )

    # CORS — always allow dev origins explicitly so 500 errors don't appear as CORS errors
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,   # must be False when allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Global exception handler — MUST include CORS header or browser sees it as CORS error
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = request.headers.get("X-Request-ID", "unknown")
        logger.error("unhandled_exception", error=str(exc), request_id=request_id)
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)[:200], "request_id": request_id},
            headers={"Access-Control-Allow-Origin": "*"},
        )

    # Routers
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(memory.router, prefix="/memory", tags=["Memory"])
    app.include_router(chat.router, prefix="/chat", tags=["Chat"])
    app.include_router(consent.router, prefix="/consent", tags=["Consent"])
    app.include_router(fhir.router, prefix="/fhir", tags=["FHIR"])
    app.include_router(admin.router, prefix="/admin", tags=["Admin"])
    app.include_router(hospital.router, prefix="/hospital", tags=["Hospital"])
    app.include_router(legal.router, prefix="/legal", tags=["Legal & Compliance"])
    app.include_router(opd.router, prefix="/opd", tags=["OPD Clinical"])
    app.include_router(ipd.router, prefix="/ipd", tags=["IPD Clinical"])
    app.include_router(nurse.router, prefix="/nurse", tags=["Nursing"])
    app.include_router(ward_bot.router, prefix="/ward-bot", tags=["Ward Bot Automations"])
    app.include_router(scheme.router, prefix="/scheme", tags=["Govt Schemes"])
    app.include_router(insurance.router, prefix="/insurance", tags=["Insurance Claims"])
    app.include_router(mlc.router, prefix="/mlc", tags=["Medico-Legal Case"])
    app.include_router(prescription.router,  prefix="/prescription",  tags=["Pharmacy"])
    app.include_router(notifications.router, prefix="/notifications",  tags=["Notifications"])
    app.include_router(activity_log.router,  prefix="/logs",           tags=["Activity Logs"])
    app.include_router(patient.router,       prefix="/patient",        tags=["Patient Search"])
    app.include_router(profile.router,       prefix="/profile",        tags=["Profile"])
    app.include_router(screening.router,     prefix="/screening",      tags=["Responsible AI Screening"])
    app.include_router(documents.router,     prefix="/documents",      tags=["Document Upload"])

    @app.get("/health", tags=["Health"])
    async def health_check():
        status = getattr(app.state, "service_status", {})
        return {
            "status": "healthy" if all(status.values()) else "degraded",
            "services": status,
        }

    return app


app = create_app()
