# 🎓 BulkCert - Automated Certificate Generation API

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

BulkCert is a high-performance, asynchronous backend service and sleek web interface designed to generate, validate, and distribute PDF certificates in bulk. Built with **FastAPI** and **ReportLab**, it features atomic concurrency safety, isolated row failures, and streamed ZIP downloads.

---

## ✨ Features


- **Bulk Processing:** Submit hundreds of recipients in a single request.
- **Atomic Concurrency:** Safe for serverless environments. Uses row-level locking to prevent duplicate processing.
- **Failure Isolation:** One invalid email or unsupported name character will fail *only* that specific certificate, allowing the rest of the batch to succeed.
- **Streamed ZIP Retrieval:** Bypasses serverless memory limits by streaming the generated PDFs and a `manifest.csv` directly to the client.
- **Custom Typography:** Bundled with open-source DejaVu fonts to support complex characters.

## 🏗️ Architecture

- **Backend:** FastAPI, Python 3.10+
- **Database:** SQLAlchemy 2.0 (SQLite for local dev, PostgreSQL for production)
- **PDF Generation:** ReportLab
- **Frontend:** HTML5, TailwindCSS, Vanilla JS

## 🚀 Local Development Setup

1. **Install dependencies:**
   Using the provided Makefile:
   ```bash
   make install
