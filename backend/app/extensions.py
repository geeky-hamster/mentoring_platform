"""SQLAlchemy engine, session factory and Alembic extension objects."""
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import config

engine = create_engine(config.cfg.DATABASE_URL, echo=config.cfg.SQL_ECHO, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


class SessionProvider:
    """Gives services a transactional session without importing HTTP objects.

    When a request runs, it needs to reuse the request's session; else standalone scripts
    use their own."
    """

    _session: Session | None = None

    def get(self) -> Session:
        return self._session


db_provider = SessionProvider()
metadata = MetaData()
