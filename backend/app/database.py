import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

DATABASE_URL = settings.DATABASE_URL

# PostgreSQL + PostGIS setup with SQLite metadata fallback for local dev fallback
try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        pass
    print(f"[+] Connected to PostgreSQL/PostGIS: {DATABASE_URL}")
    IS_POSTGIS_AVAILABLE = True
except Exception as e:
    print(f"[!] PostgreSQL+PostGIS connection to {DATABASE_URL} failed ({e}).")
    print(f"[!] Falling back to local SQLite for metadata table operations.")
    SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "nexus_local.db")
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    IS_POSTGIS_AVAILABLE = False

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
