import time
import secrets
from datetime import timedelta
from sqlalchemy import select, update, func
from app.models import Certificate, Job, CertificateFile, utcnow
from app.certificates.renderer import render_certificate, CertificateData
from app.config import settings

def claim_batch(session, job_id, n):
    sub = (select(Certificate.id).where(Certificate.job_id == job_id, Certificate.status == "PENDING")
           .order_by(Certificate.seq).limit(n).with_for_update(skip_locked=True))
    stmt = (update(Certificate).where(Certificate.id.in_(sub), Certificate.status == "PENDING")
            .values(status="PROCESSING", locked_at=utcnow(), attempts=Certificate.attempts + 1).returning(Certificate.id))
    return [row[0] for row in session.execute(stmt)]

def reclaim_stale(session, job_id):
    cutoff = utcnow() - timedelta(seconds=settings.LEASE_SECONDS)
    stmt = (update(Certificate).where(Certificate.job_id == job_id, Certificate.status == "PROCESSING", Certificate.locked_at < cutoff)
            .values(status="PENDING", locked_at=None))
    session.execute(stmt)
    session.commit()

def process_job(db_factory, job_id, budget_seconds=settings.TIME_BUDGET_SECONDS, batch_size=settings.BATCH_SIZE):
    deadline = time.monotonic() + budget_seconds
    with db_factory() as session:
        reclaim_stale(session, job_id)
        job = session.get(Job, job_id)
        if not job.started_at:
            job.started_at = utcnow()
            session.commit()

    while time.monotonic() < deadline:
        with db_factory() as session:
            ids = claim_batch(session, job_id, batch_size)
            session.commit()
            if not ids: break
            
            certs = session.execute(select(Certificate).where(Certificate.id.in_(ids))).scalars().all()
            job = session.get(Job, job_id)
            
            for cert in certs:
                try:
                    # FIX: Generate a 10-character code using valid Python secrets methods
                    code = ''.join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ234567") for _ in range(10))
                    
                    data = CertificateData(name=cert.recipient_name, course=job.course_name, issuer=job.issuer_name, issue_date=job.issue_date, verification_code=code, certificate_id=str(cert.id))
                    pdf_bytes = render_certificate(data)
                    session.add(CertificateFile(certificate_id=cert.id, data=pdf_bytes, size_bytes=len(pdf_bytes)))
                    cert.status = "COMPLETED"
                    cert.verification_code = code
                    cert.completed_at = utcnow()
                except Exception as e:
                    cert.status = "FAILED"
                    cert.failure_stage = "generation"
                    cert.error_message = str(e)
            session.commit()

    with db_factory() as session:
        if session.scalar(select(func.count()).where(Certificate.job_id == job_id, Certificate.status.in_(["PENDING", "PROCESSING"]))) == 0:
            job = session.get(Job, job_id)
            if not job.finished_at:
                job.finished_at = utcnow()
                session.commit()
