-- Runtime settings changed from the UI (e.g. the active chat model), so they
-- survive restarts. Keys absent here fall back to the environment.
CREATE TABLE IF NOT EXISTS app_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
