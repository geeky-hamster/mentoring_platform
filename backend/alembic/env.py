from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app import config as app_config
from app.models.base import Base
import app.models  # noqa: F401 - populate metadata

config_ctx = context.config

if config_ctx.config_file_name is not None:
    fileConfig(config_ctx.config_file_name)

config_ctx.set_main_option("sqlalchemy.url", app_config.cfg.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config_ctx.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config_ctx.get_section(config_ctx.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
