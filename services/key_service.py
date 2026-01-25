"""
API Key Management Service

Handles generation, validation, rotation, and revocation of API keys
for the Mycorrhizae Protocol and related Mycosoft services.
"""

from __future__ import annotations

import hashlib
import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import asyncpg


class KeyService(str, Enum):
    """Services that can have API keys."""
    MYCORRHIZAE = "mycorrhizae"
    MINDEX = "mindex"
    NATUREOS = "natureos"
    MYCOBRAIN = "mycobrain"
    MAS = "mas"
    ADMIN = "admin"


class KeyScope(str, Enum):
    """Available scopes for API keys."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    KEYS_MANAGE = "keys:manage"
    KEYS_CREATE = "keys:create"
    KEYS_REVOKE = "keys:revoke"
    DEVICE_READ = "device:read"
    DEVICE_WRITE = "device:write"
    CHANNEL_SUBSCRIBE = "channel:subscribe"
    CHANNEL_PUBLISH = "channel:publish"
    ETL_RUN = "etl:run"
    AGENT_SPAWN = "agent:spawn"


@dataclass
class APIKey:
    """Represents an API key in the system."""
    id: UUID
    key_prefix: str
    name: str
    description: Optional[str]
    owner_id: Optional[UUID]
    service: KeyService
    scopes: List[str]
    rate_limit_per_minute: int
    rate_limit_per_day: int
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    rotated_from: Optional[UUID]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_row(cls, row: asyncpg.Record) -> "APIKey":
        """Create APIKey from database row."""
        return cls(
            id=row["id"],
            key_prefix=row["key_prefix"],
            name=row["name"],
            description=row.get("description"),
            owner_id=row.get("owner_id"),
            service=KeyService(row["service"]),
            scopes=row.get("scopes", []),
            rate_limit_per_minute=row.get("rate_limit_per_minute", 60),
            rate_limit_per_day=row.get("rate_limit_per_day", 10000),
            expires_at=row.get("expires_at"),
            last_used_at=row.get("last_used_at"),
            usage_count=row.get("usage_count", 0),
            is_active=row.get("is_active", True),
            created_at=row.get("created_at", datetime.now(timezone.utc)),
            updated_at=row.get("updated_at", datetime.now(timezone.utc)),
            rotated_from=row.get("rotated_from"),
            metadata=row.get("metadata", {}),
        )
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        data = {
            "id": str(self.id),
            "key_prefix": self.key_prefix,
            "name": self.name,
            "description": self.description,
            "service": self.service.value,
            "scopes": self.scopes,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_day": self.rate_limit_per_day,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_sensitive:
            data["owner_id"] = str(self.owner_id) if self.owner_id else None
            data["rotated_from"] = str(self.rotated_from) if self.rotated_from else None
            data["metadata"] = self.metadata
        return data


@dataclass
class KeyValidationResult:
    """Result of validating an API key."""
    valid: bool
    key: Optional[APIKey] = None
    error: Optional[str] = None
    rate_limited: bool = False
    remaining_minute: Optional[int] = None
    remaining_day: Optional[int] = None


class KeyServiceManager:
    """
    Manages API keys for the Mycorrhizae Protocol.
    
    Handles:
    - Key generation with secure random tokens
    - Key validation with hash comparison
    - Key rotation with audit logging
    - Rate limiting with sliding windows
    """
    
    KEY_ALPHABET = string.ascii_letters + string.digits
    KEY_LENGTH = 32
    
    def __init__(self, db_pool: asyncpg.Pool, redis_client=None):
        self.db_pool = db_pool
        self.redis = redis_client
    
    def _generate_raw_key(self, service: KeyService) -> str:
        """Generate a new random API key."""
        random_part = ''.join(secrets.choice(self.KEY_ALPHABET) for _ in range(self.KEY_LENGTH))
        return f"myco_{service.value}_{random_part}"
    
    def _hash_key(self, raw_key: str) -> str:
        """Create SHA-256 hash of the key for storage."""
        return hashlib.sha256(raw_key.encode()).hexdigest()
    
    def _get_key_prefix(self, raw_key: str) -> str:
        """Extract displayable prefix from key."""
        return raw_key[:16] if len(raw_key) >= 16 else raw_key
    
    async def create_key(
        self,
        name: str,
        service: KeyService,
        scopes: List[str],
        owner_id: Optional[UUID] = None,
        description: Optional[str] = None,
        expires_in_days: Optional[int] = None,
        rate_limit_per_minute: int = 60,
        rate_limit_per_day: int = 10000,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, APIKey]:
        """
        Create a new API key.
        
        Returns the raw key (only shown once) and the APIKey object.
        """
        raw_key = self._generate_raw_key(service)
        key_hash = self._hash_key(raw_key)
        key_prefix = self._get_key_prefix(raw_key)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO api_keys (
                    key_hash, key_prefix, name, description, owner_id,
                    service, scopes, rate_limit_per_minute, rate_limit_per_day,
                    expires_at, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
                """,
                key_hash, key_prefix, name, description, owner_id,
                service.value, scopes, rate_limit_per_minute, rate_limit_per_day,
                expires_at, metadata or {}
            )
            
            # Log creation
            await conn.execute(
                """
                INSERT INTO api_key_audit (key_id, action, metadata)
                VALUES ($1, 'created', $2)
                """,
                row["id"],
                {"service": service.value, "scopes": scopes}
            )
        
        return raw_key, APIKey.from_row(row)
    
    async def validate_key(
        self,
        raw_key: str,
        required_scopes: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> KeyValidationResult:
        """
        Validate an API key and check rate limits.
        
        Returns validation result with key info if valid.
        """
        if not raw_key or not raw_key.startswith("myco_"):
            return KeyValidationResult(valid=False, error="Invalid key format")
        
        key_hash = self._hash_key(raw_key)
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM api_keys
                WHERE key_hash = $1 AND is_active = true
                """,
                key_hash
            )
            
            if not row:
                return KeyValidationResult(valid=False, error="Invalid or inactive key")
            
            key = APIKey.from_row(row)
            
            # Check expiration
            if key.expires_at and key.expires_at < datetime.now(timezone.utc):
                return KeyValidationResult(valid=False, error="Key has expired", key=key)
            
            # Check required scopes
            if required_scopes:
                if "admin" not in key.scopes:
                    missing = set(required_scopes) - set(key.scopes)
                    if missing:
                        return KeyValidationResult(
                            valid=False,
                            error=f"Missing required scopes: {', '.join(missing)}",
                            key=key
                        )
            
            # Check rate limits
            rate_result = await self._check_rate_limit(conn, key)
            if rate_result.rate_limited:
                await conn.execute(
                    """
                    INSERT INTO api_key_audit (key_id, action, ip_address, user_agent, endpoint, metadata)
                    VALUES ($1, 'rate_limited', $2, $3, $4, $5)
                    """,
                    key.id, ip_address, user_agent, endpoint,
                    {"remaining_minute": rate_result.remaining_minute}
                )
                return rate_result
            
            # Update usage
            await conn.execute(
                """
                UPDATE api_keys 
                SET last_used_at = NOW(), usage_count = usage_count + 1
                WHERE id = $1
                """,
                key.id
            )
            
            # Log usage
            await conn.execute(
                """
                INSERT INTO api_key_audit (key_id, action, ip_address, user_agent, endpoint)
                VALUES ($1, 'used', $2, $3, $4)
                """,
                key.id, ip_address, user_agent, endpoint
            )
            
            return KeyValidationResult(
                valid=True,
                key=key,
                remaining_minute=rate_result.remaining_minute,
                remaining_day=rate_result.remaining_day
            )
    
    async def _check_rate_limit(self, conn: asyncpg.Connection, key: APIKey) -> KeyValidationResult:
        """Check and update rate limits for a key."""
        now = datetime.now(timezone.utc)
        minute_window = now.replace(second=0, microsecond=0)
        day_window = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get current usage counts
        minute_row = await conn.fetchrow(
            """
            SELECT request_count FROM api_key_usage
            WHERE key_id = $1 AND window_start = $2 AND window_type = 'minute'
            """,
            key.id, minute_window
        )
        day_row = await conn.fetchrow(
            """
            SELECT request_count FROM api_key_usage
            WHERE key_id = $1 AND window_start = $2 AND window_type = 'day'
            """,
            key.id, day_window
        )
        
        minute_count = minute_row["request_count"] if minute_row else 0
        day_count = day_row["request_count"] if day_row else 0
        
        # Check if over limits
        if minute_count >= key.rate_limit_per_minute:
            return KeyValidationResult(
                valid=False,
                key=key,
                error="Rate limit exceeded (per minute)",
                rate_limited=True,
                remaining_minute=0,
                remaining_day=max(0, key.rate_limit_per_day - day_count)
            )
        
        if day_count >= key.rate_limit_per_day:
            return KeyValidationResult(
                valid=False,
                key=key,
                error="Rate limit exceeded (per day)",
                rate_limited=True,
                remaining_minute=0,
                remaining_day=0
            )
        
        # Update usage counts
        await conn.execute(
            """
            INSERT INTO api_key_usage (key_id, window_start, window_type, request_count)
            VALUES ($1, $2, 'minute', 1)
            ON CONFLICT (key_id, window_start, window_type)
            DO UPDATE SET request_count = api_key_usage.request_count + 1
            """,
            key.id, minute_window
        )
        await conn.execute(
            """
            INSERT INTO api_key_usage (key_id, window_start, window_type, request_count)
            VALUES ($1, $2, 'day', 1)
            ON CONFLICT (key_id, window_start, window_type)
            DO UPDATE SET request_count = api_key_usage.request_count + 1
            """,
            key.id, day_window
        )
        
        return KeyValidationResult(
            valid=True,
            key=key,
            remaining_minute=key.rate_limit_per_minute - minute_count - 1,
            remaining_day=key.rate_limit_per_day - day_count - 1
        )
    
    async def rotate_key(self, key_id: UUID, reason: Optional[str] = None) -> tuple[str, APIKey]:
        """
        Rotate an API key - create new one and invalidate old.
        
        Returns new raw key and APIKey object.
        """
        async with self.db_pool.acquire() as conn:
            # Get old key
            old_row = await conn.fetchrow(
                "SELECT * FROM api_keys WHERE id = $1",
                key_id
            )
            if not old_row:
                raise ValueError(f"Key not found: {key_id}")
            
            old_key = APIKey.from_row(old_row)
            
            # Create new key with same settings
            raw_key = self._generate_raw_key(old_key.service)
            key_hash = self._hash_key(raw_key)
            key_prefix = self._get_key_prefix(raw_key)
            
            # Insert new key
            new_row = await conn.fetchrow(
                """
                INSERT INTO api_keys (
                    key_hash, key_prefix, name, description, owner_id,
                    service, scopes, rate_limit_per_minute, rate_limit_per_day,
                    expires_at, metadata, rotated_from
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
                """,
                key_hash, key_prefix, old_key.name, old_key.description, old_key.owner_id,
                old_key.service.value, old_key.scopes, old_key.rate_limit_per_minute,
                old_key.rate_limit_per_day, old_key.expires_at, old_key.metadata, key_id
            )
            
            # Deactivate old key
            await conn.execute(
                "UPDATE api_keys SET is_active = false WHERE id = $1",
                key_id
            )
            
            # Log rotation
            await conn.execute(
                """
                INSERT INTO api_key_audit (key_id, action, metadata)
                VALUES ($1, 'rotated', $2)
                """,
                key_id,
                {"reason": reason, "new_key_id": str(new_row["id"])}
            )
        
        return raw_key, APIKey.from_row(new_row)
    
    async def revoke_key(self, key_id: UUID, reason: Optional[str] = None) -> bool:
        """Revoke (deactivate) an API key."""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE api_keys SET is_active = false WHERE id = $1",
                key_id
            )
            
            if "UPDATE 1" in result:
                await conn.execute(
                    """
                    INSERT INTO api_key_audit (key_id, action, metadata)
                    VALUES ($1, 'revoked', $2)
                    """,
                    key_id, {"reason": reason}
                )
                return True
        return False
    
    async def list_keys(
        self,
        owner_id: Optional[UUID] = None,
        service: Optional[KeyService] = None,
        include_inactive: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[APIKey]:
        """List API keys with optional filters."""
        conditions = []
        params = []
        param_idx = 1
        
        if not include_inactive:
            conditions.append(f"is_active = true")
        
        if owner_id:
            conditions.append(f"owner_id = ${param_idx}")
            params.append(owner_id)
            param_idx += 1
        
        if service:
            conditions.append(f"service = ${param_idx}")
            params.append(service.value)
            param_idx += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        params.extend([limit, offset])
        
        query = f"""
            SELECT * FROM api_keys
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [APIKey.from_row(row) for row in rows]
    
    async def get_key(self, key_id: UUID) -> Optional[APIKey]:
        """Get a specific key by ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM api_keys WHERE id = $1",
                key_id
            )
            return APIKey.from_row(row) if row else None
    
    async def get_audit_log(
        self,
        key_id: Optional[UUID] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get audit log entries for keys."""
        conditions = []
        params = []
        param_idx = 1
        
        if key_id:
            conditions.append(f"key_id = ${param_idx}")
            params.append(key_id)
            param_idx += 1
        
        if action:
            conditions.append(f"action = ${param_idx}")
            params.append(action)
            param_idx += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        
        query = f"""
            SELECT * FROM api_key_audit
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx}
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
