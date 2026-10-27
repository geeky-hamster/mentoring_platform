"""Initial schema: the exact PostgreSQL 16 DDL from the design report (17 tables, 26 FKs,
partial unique indexes, EXCLUDE-overlap constraints, triggers).

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-27
"""
from pathlib import Path

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

DDL_PATH = Path(__file__).resolve().parents[2] / "app" / "ddl" / "schema.sql"


def upgrade() -> None:
    ddl = DDL_PATH.read_text(encoding="utf-8")
    # exec_driver_sql passes the SQL to the driver verbatim (no bind-parameter parsing);
    # psycopg runs the multi-statement string via the simple query protocol.
    op.get_bind().exec_driver_sql(ddl)


def downgrade() -> None:
    op.execute("DROP SCHEMA public CASCADE")
    op.execute("CREATE SCHEMA public")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
