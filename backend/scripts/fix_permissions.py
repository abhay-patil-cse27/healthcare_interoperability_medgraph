"""Fix stale permissions — re-syncs all users' permissions from ROLE_PERMISSIONS map."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.config import get_settings
from app.models.rbac import ROLE_PERMISSIONS
from motor.motor_asyncio import AsyncIOMotorClient

async def fix():
    s  = get_settings()
    db = AsyncIOMotorClient(s.mongodb_url)[s.mongodb_db]
    count = 0
    async for user in db.users.find({}):
        role = user.get("role")
        perms_enum = ROLE_PERMISSIONS.get(role, [])
        perms = [p.value for p in perms_enum]
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"permissions": perms}}
        )
        print(f"  {user.get('full_name','?'):<30} role={role:<20} perms={len(perms)}")
        count += 1
    print(f"\nUpdated {count} users ✓")

asyncio.run(fix())
