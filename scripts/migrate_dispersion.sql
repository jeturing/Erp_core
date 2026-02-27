-- Migración: Sistema de Dispersión Mercury
-- Fecha: 2026-02-24
-- Tablas: payout_requests, system_config (si no existe)
-- ── system_config (tabla KV para feature flags y configuración dinámica) ──
CREATE TABLE IF NOT EXISTS system_config (
    key VARCHAR(128) PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    description TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW (),
    updated_by VARCHAR(255)
);

-- Valor inicial: dispersión desactivada
INSERT INTO
    system_config (key, value, description)
VALUES
    (
        'mercury_dispersion_enabled',
        'false',
        'Feature flag: activa/desactiva el sistema de dispersión Mercury'
    ) ON CONFLICT (key) DO NOTHING;

-- ── payout_requests ──
CREATE TABLE IF NOT EXISTS payout_requests (
    id SERIAL PRIMARY KEY,
    -- Datos del pago
    provider_name VARCHAR(255) NOT NULL,
    provider_account VARCHAR(64) NOT NULL,
    provider_routing VARCHAR(64) NOT NULL,
    amount_usd NUMERIC(14, 2) NOT NULL CHECK (amount_usd > 0),
    payment_method VARCHAR(32) NOT NULL DEFAULT 'ach', -- ach | wire
    concept TEXT NOT NULL,
    reference VARCHAR(128),
    notes TEXT,
    -- Ciclo de vida
    status VARCHAR(32) NOT NULL DEFAULT 'pending_approval',
    -- pending_approval → authorized → processing → completed
    --                  ↘ rejected
    --                                           ↘ failed
    -- Creación
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW (),
    -- Autorización (4-ojos)
    authorized_by VARCHAR(255),
    authorized_at TIMESTAMPTZ,
    authorization_note TEXT,
    -- Rechazo
    rejected_by VARCHAR(255),
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    -- Ejecución Mercury
    mercury_payment_id VARCHAR(128),
    executed_at TIMESTAMPTZ,
    error_message TEXT,
    -- Auditoría
    CONSTRAINT pr_status_check CHECK (
        status IN (
            'pending_approval',
            'authorized',
            'processing',
            'completed',
            'failed',
            'rejected'
        )
    ),
    CONSTRAINT pr_4eyes CHECK (
        authorized_by IS NULL
        OR authorized_by <> created_by
    )
);

CREATE INDEX IF NOT EXISTS idx_payout_status ON payout_requests (status);

CREATE INDEX IF NOT EXISTS idx_payout_created_at ON payout_requests (created_at);

CREATE INDEX IF NOT EXISTS idx_payout_created_by ON payout_requests (created_by);

COMMENT ON TABLE payout_requests IS 'Solicitudes de pago Mercury. Requieren autorización 4-ojos antes de ejecutarse.';

COMMENT ON COLUMN payout_requests.status IS 'pending_approval→authorized→processing→completed | rejected | failed';