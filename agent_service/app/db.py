from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .settings import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=2, max_overflow=1, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
