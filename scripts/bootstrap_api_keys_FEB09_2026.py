"""
Bootstrap API keys for Mycorrhizae (stores keys in Postgres).

Why this exists:
- Mycorrhizae has a full /api/keys CRUD API, but you need an *admin* key to create keys.
- This script creates the FIRST admin key (and optional service keys) directly in the DB.

Notes:
- Secrets are printed to stdout (only time you will see them). Do not commit output.
- The canonical DB for Mycosoft is MINDEX Postgres on VM 192.168.0.189.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import secrets
from typing import Iterable

import asyncpg

from services.key_service import KeyServiceManager, KeyService


SCHEMA_SQL: str = """
-- Minimal schema required by services/key_service.py
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key_hash text UNIQUE NOT NULL,
  key_prefix text NOT NULL,
  name text NOT NULL,
  description text,
  owner_id uuid,
  service text NOT NULL,
  scopes jsonb NOT NULL DEFAULT '[]'::jsonb,
  rate_limit_per_minute integer NOT NULL DEFAULT 60,
  rate_limit_per_day integer NOT NULL DEFAULT 10000,
  expires_at timestamptz,
  last_used_at timestamptz,
  usage_count integer NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  rotated_from uuid REFERENCES api_keys(id),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_api_keys_service ON api_keys(service);
CREATE INDEX IF NOT EXISTS ix_api_keys_active ON api_keys(is_active);

CREATE TABLE IF NOT EXISTS api_key_usage (
  key_id uuid NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  window_start timestamptz NOT NULL,
  window_type text NOT NULL,
  request_count integer NOT NULL DEFAULT 0,
  PRIMARY KEY (key_id, window_start, window_type)
);

CREATE TABLE IF NOT EXISTS api_key_audit (
  id bigserial PRIMARY KEY,
  key_id uuid NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  action text NOT NULL,
  ip_address inet,
  user_agent text,
  endpoint text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);
"""


def _split_sql(sql: str) -> Iterable[str]:
    # Good enough for this constrained schema file (no function bodies).
    for stmt in sql.split(";"):
        s = stmt.strip()
        if s:
            yield s + ";"


def _random_env_key(prefix: str) -> str:
    # Matches the overall style used by KeyServiceManager (human-readable + random).
    return f"{prefix}_{secrets.token_urlsafe(24)}"


async def _ensure_schema(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        for stmt in _split_sql(SCHEMA_SQL):
            await conn.execute(stmt)


async def _create_mycorrhizae_key(
    key_svc: KeyServiceManager,
    *,
    name: str,
    service: KeyService,
    scopes: list[str],
    description: str | None,
) -> str:
    raw_key, _ = await key_svc.create_key(
        name=name,
        service=service,
        scopes=scopes,
        description=description,
        expires_in_days=None,
        rate_limit_per_minute=600,
        rate_limit_per_day=50000,
        metadata={"created_by": "bootstrap_api_keys_FEB09_2026.py"},
    )
    return raw_key


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database-url",
        default=os.getenv("MYCORRHIZAE_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="Postgres URL. Defaults to MYCORRHIZAE_DATABASE_URL (or DATABASE_URL).",
    )
    parser.add_argument(
        "--ensure-schema",
        action="store_true",
        help="Create api_keys/api_key_usage/api_key_audit tables if missing.",
    )
    parser.add_argument(
        "--create-admin",
        action="store_true",
        help="Create the FIRST admin key (fails if any key already exists).",
    )
    parser.add_argument(
        "--create-service",
        action="append",
        default=[],
        help="Create a service key stored in Mycorrhizae (e.g. --create-service mas).",
    )
    parser.add_argument(
        "--print-mindex-api-key",
        action="store_true",
        help="Print a random MINDEX_API_KEY value (MINDEX reads it from env).",
    )
    args = parser.parse_args()

    if not args.database_url:
        raise SystemExit("Missing --database-url (or MYCORRHIZAE_DATABASE_URL).")

    pool = await asyncpg.create_pool(args.database_url, min_size=1, max_size=3)
    try:
        if args.ensure_schema:
            await _ensure_schema(pool)

        key_svc = KeyServiceManager(db_pool=pool)

        if args.create_admin:
            if await key_svc.has_any_keys():
                raise SystemExit("Refusing to create admin key: keys already exist in DB.")

            raw_admin = await _create_mycorrhizae_key(
                key_svc,
                name="bootstrap-admin",
                service=KeyService.ADMIN,
                scopes=["admin", "keys:manage", "keys:create", "keys:revoke", "read", "write"],
                description="First admin key (bootstrap). Store securely; rotate after setup.",
            )
            print(f"MYCORRHIZAE_ADMIN_API_KEY={raw_admin}")

        for svc in args.create_service:
            try:
                service = KeyService(svc)
            except ValueError:
                raise SystemExit(f"Invalid --create-service '{svc}'. Valid: {[s.value for s in KeyService]}")

            raw = await _create_mycorrhizae_key(
                key_svc,
                name=f"{service.value}-service",
                service=service,
                scopes=["read", "write"],
                description=f"Service key for {service.value} -> Mycorrhizae calls.",
            )
            # This is the one you wire into MAS as MYCORRHIZAE_API_KEY, etc.
            print(f"MYCORRHIZAE_API_KEY__FOR_{service.value.upper()}={raw}")

        if args.print_mindex_api_key:
            # MINDEX API keys are env-configured (not stored in DB).
            print(f"MINDEX_API_KEY={_random_env_key('myco_mindex')}")

        return 0
    finally:
        await pool.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

