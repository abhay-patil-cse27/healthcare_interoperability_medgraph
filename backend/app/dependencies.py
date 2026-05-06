from fastapi import Depends, HTTPException, Header
from typing import Annotated, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from functools import lru_cache
from app.config import get_settings
from app.utils.jwt_handler import decode_access_token


@lru_cache()
def get_mongo_client() -> AsyncIOMotorClient:
    settings = get_settings()
    return AsyncIOMotorClient(settings.mongodb_url)


async def get_db() -> AsyncIOMotorDatabase:
    settings = get_settings()
    client = get_mongo_client()
    return client[settings.mongodb_db]


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    db=Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )

    token = authorization.split(" ")[1]
    claims = decode_access_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = await db.users.find_one({"user_id": claims["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Auto-populate permissions array on the user object if not present (backward compatibility)
    from app.models.rbac import ROLE_PERMISSIONS, UserRole
    if "permissions" not in user or not user["permissions"]:
        try:
            role_enum = UserRole(user["role"])
            user["permissions"] = [p.value for p in ROLE_PERMISSIONS.get(role_enum, [])]
        except ValueError:
            user["permissions"] = []
            
    # Include token claims for zero-latency checks if we want to rely on them
    user["token_permissions"] = claims.get("permissions", [])

    return user

def require_permission(required_permission: str):
    """
    Permission-based guard pattern. 
    Checks if the user has the required permission either embedded in the JWT 
    or dynamically pulled from the DB.
    """
    async def permission_checker(current_user=Depends(get_current_user)):
        # Check token first (zero-latency)
        if required_permission in current_user.get("token_permissions", []):
            return current_user
            
        # Fallback to DB permissions (for newly granted perms or old tokens)
        if required_permission in current_user.get("permissions", []):
            return current_user
            
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Missing permission: {required_permission}"
        )
    return permission_checker

def require_any_permission(permissions: list[str]):
    """
    Checks if the user has AT LEAST ONE of the required permissions.
    """
    async def permission_checker(current_user=Depends(get_current_user)):
        for required_permission in permissions:
            if required_permission in current_user.get("token_permissions", []):
                return current_user
            if required_permission in current_user.get("permissions", []):
                return current_user
        
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Missing one of permissions: {', '.join(permissions)}"
        )
    return permission_checker

