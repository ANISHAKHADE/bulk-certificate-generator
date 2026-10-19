from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from pathlib import Path
from app.db import init_db
from app.api.jobs import router as jobs_router

# FIX: Force DB initialization immediately when Vercel loads the file
try:
    init_db()
    print("Database tables verified/created successfully.")
except Exception as e:
    print(f"CRITICAL DB ERROR: {e}")

app = FastAPI(title="Bulk Certificate Generator")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": "Request validation failed", "details": exc.errors()}}
    )

app.include_router(jobs_router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_frontend():
    html_path = Path(__file__).parent / "frontend" / "index.html"
    return html_path.read_text(encoding="utf-8")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
