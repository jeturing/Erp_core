"""
Alembic environment configuration for ERP Core.
Loads the correct .env file based on ERP_ENV, then uses DATABASE_URL.

Usage:
  ERP_ENV=test alembic upgrade head        # → .env.test (BD 10.10.10.20)
  ERP_ENV=production alembic upgrade head  # → .env.production (BD HA 10.10.10.137)
  alembic upgrade head                     # → .env (dev default)
  DATABASE_URL=... alembic upgrade head    # → explicit override
"""
import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure the project root is in sys.path so we can import app.models
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

from dotenv import load_dotenv

# ── Select .env file based on ERP_ENV ──
_erp_env = os.getenv("ERP_ENV", "development").lower().strip()
_env_files = {
    "development": os.path.join(_project_root, ".env"),
    "test":        os.path.join(_project_root, ".env.test"),
    "production":  os.path.join(_project_root, ".env.production"),
}
_env_file = _env_files.get(_erp_env, os.path.join(_project_root, ".env"))
if os.path.exists(_env_file):
    load_dotenv(_env_file, override=True)
else:
    load_dotenv(override=True)

# Alembic Config object
config = context.config

# Override sqlalchemy.url from env var if present
_raw = os.getenv("DATABASE_URL", "")
if _raw:
    # Normalize to psycopg2 driver (available on this system)
    if "+psycopg" in _raw and "+psycopg2" not in _raw:
        _raw = _raw.replace("+psycopg://", "+psycopg2://", 1)
    elif _raw.startswith("postgresql://"):
        _raw = _raw.replace("postgresql://", "postgresql+psycopg2://", 1)
    config.set_main_option("sqlalchemy.url", _raw)

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import ALL models so Alembic can detect them for autogenerate
from app.models.database import Base  # noqa: E402

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script generation)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (against live DB)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"client_encoding": "utf8"},
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,           # Detect column type changes
            compare_server_default=True, # Detect default value changes
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
