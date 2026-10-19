import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, ForeignKey, DateTime, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_name: Mapped[str] = mapped_column(String(150))
    issuer_name: Mapped[str] = mapped_column(String(150))
    issue_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

class Certificate(Base):
    __tablename__ = "certificates"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    recipient_name: Mapped[str] = mapped_column(String(200))
    recipient_email: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(16), default="PENDING", index=True)
    failure_stage: Mapped[str] = mapped_column(String(16), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    verification_code: Mapped[str] = mapped_column(String(16), nullable=True, unique=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

class CertificateFile(Base):
    __tablename__ = "certificate_files"
    certificate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("certificates.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary)
    size_bytes: Mapped[int] = mapped_column(Integer)
