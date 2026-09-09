"""
TraceRx AI - Database Schema (PostgreSQL / Supabase / SQLite)
Stores enterprise organizations, off-chain batch metadata, custody checkpoints, and audit logs.
"""

import time
from typing import Generator
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from backend.app.core.config import settings

Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(64), primary_key=True, index=True)
    tenant_id = Column(String(64), index=True, default=settings.DEFAULT_TENANT_ID)
    name = Column(String(128), nullable=False)
    role = Column(String(32), nullable=False)  # Manufacturer, Distributor, Pharmacy, Regulator
    evm_address = Column(String(42), unique=True, index=True)
    gln = Column(String(32), nullable=True)     # GS1 Global Location Number
    country = Column(String(4), default="US")
    created_at = Column(Float, default=time.time)


class BatchRecord(Base):
    __tablename__ = "batches"

    id = Column(String(64), primary_key=True, index=True)  # e.g. PZ-2026-X99
    tenant_id = Column(String(64), index=True, default=settings.DEFAULT_TENANT_ID)
    gtin = Column(String(14), index=True, nullable=False)   # (01) GTIN
    batch_lot = Column(String(32), index=True, nullable=False)  # (10) Lot
    serial_number = Column(String(64), index=True, nullable=True)  # (21) Serial
    expiry_date = Column(String(16), nullable=False)        # (17) YYMMDD or YYYY-MM-DD
    drug_name = Column(String(128), nullable=False)
    merkle_root = Column(String(66), nullable=False)
    status = Column(String(32), default="ACTIVE")          # ACTIVE, DISPENSED, RECALLED
    current_custodian = Column(String(42), nullable=False)
    manufacturer_address = Column(String(42), nullable=False)
    on_chain_tx = Column(String(66), nullable=True)
    created_at = Column(Float, default=time.time)
    dispensed_at = Column(Float, nullable=True)
    dispensed_location = Column(String(128), nullable=True)

    custody_events = relationship("CustodyEvent", back_populates="batch", cascade="all, delete-orphan")


class CustodyEvent(Base):
    __tablename__ = "custody_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), ForeignKey("batches.id"), index=True)
    from_entity = Column(String(128), nullable=False)
    to_entity = Column(String(128), nullable=False)
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42), nullable=False)
    location = Column(String(128), nullable=False)
    signature = Column(Text, nullable=False)
    tx_hash = Column(String(66), nullable=True)
    timestamp = Column(Float, default=time.time)

    batch = relationship("BatchRecord", back_populates="custody_events")


class ScanAuditLog(Base):
    __tablename__ = "scan_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scanner_id = Column(String(64), index=True)
    location = Column(String(128), nullable=False)
    batch_id = Column(String(64), index=True, nullable=True)
    authenticity_score = Column(Float, nullable=False)
    tampering_index = Column(Float, nullable=False)
    print_dpi = Column(Integer, default=600)
    verdict = Column(String(64), nullable=False)
    duplicate_reuse_flag = Column(Boolean, default=False)
    timestamp = Column(Float, default=time.time)


# Database Engine setup
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
