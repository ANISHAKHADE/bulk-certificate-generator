from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from .config import settings

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://") or db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://").replace("postgresql://", "postgresql+psycopg://")

engine_kwargs = {}
if settings.SERVERLESS:
    engine_kwargs["poolclass"] = NullPool
if db_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}

engine = create_engine(db_url, **engine_kwargs)

if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
