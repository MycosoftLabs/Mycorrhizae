-- 001_api_keys_schema_OCT03_2026.sql
--
-- API key store for the Mycorrhizae Protocol (services/key_service.py):
-- issuance, validation, rotation, revocation, audit log and rate-limit windows.
--
-- The tables live in their own `mycorrhizae` schema. MINDEX Postgres already has
-- `mycosoft.api_keys`, owned by the MAS api_keys router with a different shape, and
-- the `mycosoft` role resolves unqualified `api_keys` to it via "$user" in search_path.
-- The API pins search_path to MYCORRHIZAE_DB_SCHEMA (default `mycorrhizae`).
--
-- Idempotent. Apply with:
--   psql "$MYCORRHIZAE_DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/001_api_keys_schema_OCT03_2026.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS mycorrhizae;

CREATE TABLE IF NOT EXISTS mycorrhizae.api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  key_hash text UNIQUE NOT NULL,
  key_prefix text NOT NULL,
  name text NOT NULL,
  description text,
  owner_id uuid,
  service text NOT NULL
    CHECK (service IN ('mycorrhizae', 'mindex', 'natureos', 'mycobrain', 'mas', 'admin')),
  scopes jsonb NOT NULL DEFAULT '[]'::jsonb,
  rate_limit_per_minute integer NOT NULL DEFAULT 60,
  rate_limit_per_day integer NOT NULL DEFAULT 10000,
  expires_at timestamptz,
  last_used_at timestamptz,
  usage_count integer NOT NULL DEFAULT 0,
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  rotated_from uuid REFERENCES mycorrhizae.api_keys(id),
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_api_keys_service ON mycorrhizae.api_keys(service);
CREATE INDEX IF NOT EXISTS ix_api_keys_is_active ON mycorrhizae.api_keys(is_active);

CREATE TABLE IF NOT EXISTS mycorrhizae.api_key_usage (
  key_id uuid NOT NULL REFERENCES mycorrhizae.api_keys(id) ON DELETE CASCADE,
  window_start timestamptz NOT NULL,
  window_type text NOT NULL CHECK (window_type IN ('minute', 'day')),
  request_count integer NOT NULL DEFAULT 0,
  PRIMARY KEY (key_id, window_start, window_type)
);

CREATE TABLE IF NOT EXISTS mycorrhizae.api_key_audit (
  id bigserial PRIMARY KEY,
  key_id uuid NOT NULL REFERENCES mycorrhizae.api_keys(id) ON DELETE CASCADE,
  action text NOT NULL,
  ip_address inet,
  user_agent text,
  endpoint text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_api_key_audit_key_created
  ON mycorrhizae.api_key_audit(key_id, created_at DESC);

CREATE OR REPLACE FUNCTION mycorrhizae.touch_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_api_keys_updated_at ON mycorrhizae.api_keys;
CREATE TRIGGER trg_api_keys_updated_at
  BEFORE UPDATE ON mycorrhizae.api_keys
  FOR EACH ROW EXECUTE FUNCTION mycorrhizae.touch_updated_at();

COMMIT;
