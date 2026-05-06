import asyncio
import os
import sys
from datetime import datetime
import uuid

# Add the backend dir to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.rbac import UserRole, ROLE_PERMISSIONS
from app.models.user import UserInDB
from app.utils.jwt_handler import get_password_hash
from app.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient

async def seed_super_admin():
    settings = get_settings()
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_db]

    email = "superadmin@india.gov.in"
    password = "SuperSecurePassword123!"

    existing = await db.users.find_one({"email": email})
    if existing:
        print(f"Super admin {email} already exists. Exiting.")
        return

    permissions = [p.value for p in ROLE_PERMISSIONS.get(UserRole.SUPER_ADMIN, [])]

    super_admin = UserInDB(
        user_id=str(uuid.uuid4()),
        email=email,
        hashed_password=get_password_hash(password),
        full_name="MoHFW System Admin",
        role=UserRole.SUPER_ADMIN,
        permissions=permissions,
        created_at=datetime.utcnow()
    )

    await db.users.insert_one(super_admin.model_dump())
    print(f"Successfully seeded super admin!")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Role: {UserRole.SUPER_ADMIN}")

if __name__ == "__main__":
    asyncio.run(seed_super_admin())
