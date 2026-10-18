CREATE TABLE IF NOT EXISTS cc_messages (
  room_id TEXT NOT NULL, message_id TEXT NOT NULL, account_id TEXT,
  name TEXT NOT NULL, body TEXT NOT NULL, send_time TIMESTAMPTZ NOT NULL,
  content_hash TEXT NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(room_id, message_id)
);
CREATE INDEX IF NOT EXISTS cc_messages_period ON cc_messages(room_id, send_time);
CREATE TABLE IF NOT EXISTS cc_message_versions (
  version_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  room_id TEXT NOT NULL, message_id TEXT NOT NULL, body TEXT NOT NULL,
  content_hash TEXT NOT NULL, metadata JSONB NOT NULL DEFAULT '{}',
  version_time TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE cc_message_versions ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}';
CREATE TABLE IF NOT EXISTS cc_settings (key TEXT PRIMARY KEY, value JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS cc_sessions (
  session_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE,
  room_id TEXT NOT NULL, month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
  year INTEGER NOT NULL CHECK(year BETWEEN 2000 AND 2100),
  status TEXT NOT NULL DEFAULT 'prepared', snapshot JSONB NOT NULL,
  ai_settings JSONB NOT NULL, raw_events JSONB NOT NULL DEFAULT '[]',
  completed JSONB NOT NULL DEFAULT '[]', results JSONB NOT NULL DEFAULT '[]',
  error_message TEXT, is_draft BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cc_files (
  session_id TEXT PRIMARY KEY REFERENCES cc_sessions(session_id),
  filename TEXT NOT NULL, content BYTEA NOT NULL, sha256 TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cc_leases (
  resource TEXT PRIMARY KEY, owner_token TEXT NOT NULL, expires_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS cc_actions (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  kind TEXT NOT NULL, status TEXT NOT NULL, session_id TEXT, summary TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}', created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cc_login_attempts (
  fingerprint TEXT PRIMARY KEY, attempts INTEGER NOT NULL,
  window_start TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS cc_auth_sessions (
  token_digest TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS cc_auth_sessions_expiry ON cc_auth_sessions(expires_at);
