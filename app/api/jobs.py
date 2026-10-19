import io, zipfile, csv, uuid
from collections import deque
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db import get_db, SessionLocal
from app.schemas import JobCreate
from app.services.jobs import create_job, get_job_summary, NoValidRecipients
from app.services.processor import process_job
from app.models import Certificate, CertificateFile
from app.config import settings

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])

@router.post("", status_code=202)
def create_job_endpoint(payload: JobCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try: job = create_job(db, payload.course_name, payload.issuer_name, payload.issue_date, payload.recipients)
    except NoValidRecipients as e: return JSONResponse(status_code=422, content={"error": {"code": "validation_error", "message": "No valid recipients", "details": e.errors}})
    
    if settings.PROCESSING_MODE == "inline": process_job(SessionLocal, job.id)
    else: background_tasks.add_task(process_job, SessionLocal, job.id)
        
    return JSONResponse(status_code=202, content=get_job_summary(db, job.id), headers={"Location": f"/api/v1/jobs/{job.id}"})

# FIX: Changed job_id: str to job_id: uuid.UUID
@router.get("/{job_id}")
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db)):
    summary = get_job_summary(db, job_id)
    if not summary: raise HTTPException(404, "Job not found")
    return summary

class _Sink(io.RawIOBase):
    def __init__(self): self.chunks = deque(); self._pos = 0
    def writable(self): return True
    def write(self, b): self.chunks.append(bytes(b)); self._pos += len(b); return len(b)
    def tell(self): return self._pos
    def flush(self): pass
    def drain(self):
        while self.chunks: yield self.chunks.popleft()

# FIX: Changed job_id: str to job_id: uuid.UUID
@router.get("/{job_id}/download")
def download_job_zip(job_id: uuid.UUID, partial: bool = False):
    def stream_zip():
        sink = _Sink()
        with SessionLocal() as db:
            summary = get_job_summary(db, job_id)
            if not summary: raise HTTPException(404)
            if summary["status"] in ["QUEUED", "PROCESSING"] and not partial: raise HTTPException(409, "Job is still processing")
                
            certs = db.execute(select(Certificate).where(Certificate.job_id == job_id).order_by(Certificate.seq)).scalars().all()
            with zipfile.ZipFile(sink, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
                manifest = io.StringIO(); writer = csv.writer(manifest)
                writer.writerow(["index", "name", "email", "status", "verification_code", "error"])
                for c in certs: writer.writerow([c.seq, c.recipient_name, c.recipient_email, c.status, c.verification_code, c.error_message])
                zf.writestr("manifest.csv", manifest.getvalue())
                yield from sink.drain()

                for c in certs:
                    if c.status == "COMPLETED":
                        file_record = db.get(CertificateFile, c.id)
                        if file_record:
                            safe_name = "".join(x for x in c.recipient_name if x.isalnum() or x in " -_").strip()
                            zf.writestr(f"{c.seq+1:04d}-{safe_name}-{c.verification_code}.pdf", file_record.data)
                            yield from sink.drain()
        yield from sink.drain()
    # FIX: Cast job_id to string for the filename
    return StreamingResponse(stream_zip(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="certificates-{str(job_id)[:8]}.zip"'})
