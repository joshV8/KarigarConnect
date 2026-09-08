import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL, ENVIRONMENT

logger = logging.getLogger("artisan.database")

# Normalize postgres:// to postgresql:// for hosted PostgreSQL compatibility (e.g. Render/Railway)
db_url = DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Connection pooling settings optimized for hackathon production / hosted DBs
engine_kwargs = {
    "pool_pre_ping": True,     # Automatically reconnects dropped/stale connections
    "pool_recycle": 300,       # Recycle connections every 5 minutes to prevent provider timeouts
}

# SQLite fallback support for quick zero-config local tests
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(db_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides an isolated database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
