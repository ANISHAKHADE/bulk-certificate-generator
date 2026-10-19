from sqlalchemy import select, func
from app.models import Job, Certificate
from app.services.validation import validate_recipients
from app.config import settings
from datetime import datetime, timezone

class NoValidRecipients(Exception):
    def __init__(self, errors): self.errors = errors

def create_job(db, course_name, issuer_name, issue_date, raw_recipients):
    validated = validate_recipients(raw_recipients)
    if all(r.errors for r in validated):
        raise NoValidRecipients([{"index": r.index, "errors": r.errors} for r in validated[:50]])

    job = Job(course_name=course_name, issuer_name=issuer_name or settings.DEFAULT_ISSUER_NAME, issue_date=issue_date or datetime.now(timezone.utc), total=len(validated))
    db.add(job)
    db.flush()

    certs = [{"job_id": job.id, "seq": r.index, "recipient_name": r.name, "recipient_email": r.email, "status": "FAILED" if r.errors else "PENDING", "failure_stage": "validation" if r.errors else None, "error_message": "; ".join(r.errors) if r.errors else None} for r in validated]
    db.execute(Certificate.__table__.insert(), certs)
    db.commit()
    return job

def get_job_summary(db, job_id):
    job = db.get(Job, job_id)
    if not job: return None
    counts_query = db.execute(select(Certificate.status, func.count()).where(Certificate.job_id == job_id).group_by(Certificate.status)).all()
    counts = {"total": job.total, "pending": 0, "processing": 0, "completed": 0, "failed": 0}
    for status, c in counts_query: counts[status.lower()] = c
        
    if not job.started_at and (counts["pending"] + counts["processing"]) > 0: status = "QUEUED"
    elif (counts["pending"] + counts["processing"]) > 0: status = "PROCESSING"
    elif counts["completed"] == 0: status = "FAILED"
    elif counts["failed"] == 0: status = "COMPLETED"
    else: status = "COMPLETED_WITH_ERRORS"

    progress = (counts["completed"] + counts["failed"]) / job.total * 100 if job.total else 0
    failures = db.execute(select(Certificate).where(Certificate.job_id == job_id, Certificate.status == "FAILED").limit(20)).scalars().all()
    
    return {"job_id": str(job.id), "status": status, "course_name": job.course_name, "issuer_name": job.issuer_name, "issue_date": job.issue_date.isoformat(), "counts": counts, "progress_percent": round(progress, 1), "created_at": job.created_at.isoformat(), "failures_preview": [{"index": f.seq, "name": f.recipient_name, "error": f.error_message} for f in failures]}
