from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'invoices.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def ensure_invoice_columns() -> None:
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(invoices)"))
        existing_columns = {row[1] for row in result}
        if "igst" not in existing_columns:
            conn.execute(text("ALTER TABLE invoices ADD COLUMN igst TEXT"))