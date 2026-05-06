import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = structlog.get_logger()


async def ping_mongodb(db: AsyncIOMotorDatabase) -> bool:
    try:
        await db.command("ping")
        return True
    except Exception as e:
        logger.error("mongodb_ping_failed", error=str(e))
        return False
