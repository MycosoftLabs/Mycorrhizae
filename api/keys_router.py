"""
API Key Management Endpoints

Full CRUD operations for API keys with rate limiting and audit logging.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field

from services.key_service import KeyServiceManager, KeyService, APIKey, KeyScope


router = APIRouter()


# ==================== Pydantic Models ====================

class CreateKeyRequest(BaseModel):
    """Request to create a new API key."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    service: str = Field(..., pattern="^(mycorrhizae|mindex|natureos|mycobrain|mas|admin)$")
    scopes: List[str] = Field(default=["read"])
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    rate_limit_per_day: int = Field(default=10000, ge=1, le=1000000)
    expires_in_days: Optional[int] = Field(default=None, ge=1, le=365)


class KeyResponse(BaseModel):
    """API key response (without secret)."""
    id: str
    key_prefix: str
    name: str
    description: Optional[str]
    service: str
    scopes: List[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    expires_at: Optional[str]
    last_used_at: Optional[str]
    usage_count: int
    is_active: bool
    created_at: str


class CreateKeyResponse(BaseModel):
    """Response when creating a key - includes the raw key (only shown once)."""
    key: str  # The raw key - ONLY SHOWN ONCE
    id: str
    key_prefix: str
    name: str
    service: str
    scopes: List[str]
    message: str = "Store this key securely - it will not be shown again"


class ValidateKeyRequest(BaseModel):
    """Request to validate an API key."""
    key: str
    required_scopes: Optional[List[str]] = None


class ValidateKeyResponse(BaseModel):
    """Response from key validation."""
    valid: bool
    error: Optional[str] = None
    key_id: Optional[str] = None
    service: Optional[str] = None
    scopes: Optional[List[str]] = None
    remaining_minute: Optional[int] = None
    remaining_day: Optional[int] = None


class RotateKeyResponse(BaseModel):
    """Response when rotating a key."""
    new_key: str
    new_key_id: str
    old_key_id: str
    message: str = "Old key has been deactivated. Store new key securely."


class AuditLogEntry(BaseModel):
    """An entry in the audit log."""
    id: int
    key_id: str
    action: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    created_at: str


# ==================== Dependencies ====================

async def get_key_service_dep() -> KeyServiceManager:
    """Dependency to get key service."""
    from api.main import get_key_service
    return await get_key_service()


async def validate_admin_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
) -> APIKey:
    """Validate that the request has an admin API key."""
    result = await key_svc.validate_key(
        raw_key=x_api_key,
        required_scopes=["admin", "keys:manage"],
    )
    if not result.valid:
        raise HTTPException(status_code=403, detail=result.error)
    return result.key


# ==================== Endpoints ====================

@router.post("", response_model=CreateKeyResponse)
async def create_key(
    request: CreateKeyRequest,
    req: Request,
    admin_key: APIKey = Depends(validate_admin_key),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
):
    """
    Create a new API key.
    
    Requires admin scope. The raw key is only returned once.
    """
    raw_key, api_key = await key_svc.create_key(
        name=request.name,
        service=KeyService(request.service),
        scopes=request.scopes,
        description=request.description,
        expires_in_days=request.expires_in_days,
        rate_limit_per_minute=request.rate_limit_per_minute,
        rate_limit_per_day=request.rate_limit_per_day,
    )
    
    return CreateKeyResponse(
        key=raw_key,
        id=str(api_key.id),
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        service=api_key.service.value,
        scopes=api_key.scopes,
    )


@router.get("", response_model=List[KeyResponse])
async def list_keys(
    service: Optional[str] = None,
    include_inactive: bool = False,
    limit: int = 100,
    offset: int = 0,
    admin_key: APIKey = Depends(validate_admin_key),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
):
    """List all API keys (admin only)."""
    service_filter = KeyService(service) if service else None
    
    keys = await key_svc.list_keys(
        service=service_filter,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )
    
    return [
        KeyResponse(
            id=str(k.id),
            key_prefix=k.key_prefix,
            name=k.name,
            description=k.description,
            service=k.service.value,
            scopes=k.scopes,
            rate_limit_per_minute=k.rate_limit_per_minute,
            rate_limit_per_day=k.rate_limit_per_day,
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            usage_count=k.usage_count,
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]


@router.get("/{key_id}", response_model=KeyResponse)
async def get_key(
    key_id: UUID,
    admin_key: APIKey = Depends(validate_admin_key),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
):
    """Get details for a specific key."""
    k = await key_svc.get_key(key_id)
    if not k:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return KeyResponse(
        id=str(k.id),
        key_prefix=k.key_prefix,
        name=k.name,
        description=k.description,
        service=k.service.value,
        scopes=k.scopes,
        rate_limit_per_minute=k.rate_limit_per_minute,
        rate_limit_per_day=k.rate_limit_per_day,
        expires_at=k.expires_at.isoformat() if k.expires_at else None,
        last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        usage_count=k.usage_count,
        is_active=k.is_active,
        created_at=k.created_at.isoformat(),
    )


@router.post("/{key_id}/rotate", response_model=RotateKeyResponse)
async def rotate_key(
    key_id: UUID,
    reason: Optional[str] = None,
    admin_key: APIKey = Depends(validate_admin_key),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
):
    """
    Rotate an API key.
    
    Creates a new key with the same settings and deactivates the old one.
    """
    try:
        new_raw_key, new_key = await key_svc.rotate_key(key_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return RotateKeyResponse(
        new_key=new_raw_key,
        new_key_id=str(new_key.id),
        old_key_id=str(key_id),
    )


@router.delete("/{key_id}")
async def revoke_key(
    key_id: UUID,
    reason: Optional[str] = None,
    admin_key: APIKey = Depends(validate_admin_key),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
):
    """Revoke (deactivate) an API key."""
    success = await key_svc.revoke_key(key_id, reason)
    if not success:
        raise HTTPException(status_code=404, detail="Key not found")
    
    return {"status": "revoked", "key_id": str(key_id)}


@router.post("/validate", response_model=ValidateKeyResponse)
async def validate_key(
    request: ValidateKeyRequest,
    req: Request,
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
):
    """
    Validate an API key and check permissions.
    
    Does not require admin access - used for self-validation.
    """
    result = await key_svc.validate_key(
        raw_key=request.key,
        required_scopes=request.required_scopes,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
    )
    
    return ValidateKeyResponse(
        valid=result.valid,
        error=result.error,
        key_id=str(result.key.id) if result.key else None,
        service=result.key.service.value if result.key else None,
        scopes=result.key.scopes if result.key else None,
        remaining_minute=result.remaining_minute,
        remaining_day=result.remaining_day,
    )


@router.get("/{key_id}/audit", response_model=List[AuditLogEntry])
async def get_key_audit_log(
    key_id: UUID,
    action: Optional[str] = None,
    limit: int = 100,
    admin_key: APIKey = Depends(validate_admin_key),
    key_svc: KeyServiceManager = Depends(get_key_service_dep),
):
    """Get audit log for a specific key."""
    logs = await key_svc.get_audit_log(key_id=key_id, action=action, limit=limit)
    
    return [
        AuditLogEntry(
            id=log["id"],
            key_id=str(log["key_id"]),
            action=log["action"],
            ip_address=str(log["ip_address"]) if log.get("ip_address") else None,
            user_agent=log.get("user_agent"),
            endpoint=log.get("endpoint"),
            created_at=log["created_at"].isoformat() if log.get("created_at") else "",
        )
        for log in logs
    ]
