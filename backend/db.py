from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from pathlib import Path
import os


# ============================================================
# LOAD .env FROM THE BACKEND FOLDER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================
# CHECK DATABASE URL
# ============================================================

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL was not found.\n"
        f"Please check your .env file:\n"
        f"{ENV_FILE}"
    )


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={
        "statement_cache_size": 0
    }
)


# ============================================================
# ASYNC SESSION
# ============================================================

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ============================================================
# BASE MODEL
# ============================================================

Base = declarative_base()