import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from services.pdf_processor import extract_text_from_pdf, get_pdf_page_count
from services.vector_store import add_chunks, delete_document, list_documents, get_total_chunks
from services.rag_pipeline import run_rag_pipeline
from services.report_generator import generate_report
from services.guardrails import check_input

load_dotenv()

# API key read from .env — never sent from frontend
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

app = FastAPI(title="Enterprise RAG API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


class QueryRequest(BaseModel):
    query: str

class ReportRequest(BaseModel):
    topic: str
    answer: str
    chunks: list[dict]

class GuardrailTestRequest(BaseModel):
    query: str


@app.get("/health")
def health():
    key_set = bool(OPENROUTER_API_KEY)
    return {"status": "ok", "version": "2.0.0", "api_key_configured": key_set}

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    document_id = str(uuid.uuid4())[:8]
    save_path = os.path.join(UPLOAD_DIR, f"{document_id}_{file.filename}")
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        chunks = extract_text_from_pdf(save_path)
        page_count = get_pdf_page_count(save_path)
        add_chunks(document_id, file.filename, chunks)
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    return {
        "success": True, "document_id": document_id,
        "filename": file.filename, "pages": page_count,
        "chunks_added": len(chunks),
        "message": f"Indexed {len(chunks)} chunks from {page_count} pages."
    }

@app.get("/documents")
def get_documents():
    return {"documents": list_documents(), "total_chunks": get_total_chunks()}

@app.delete("/document/{document_id}")
def remove_document(document_id: str):
    try:
        delete_document(document_id)
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(document_id):
                os.remove(os.path.join(UPLOAD_DIR, f))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"success": True, "message": f"Document {document_id} deleted."}

@app.put("/document/{document_id}")
async def update_document(document_id: str, file: UploadFile = File(...)):
    delete_document(document_id)
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(document_id):
            os.remove(os.path.join(UPLOAD_DIR, f))
    save_path = os.path.join(UPLOAD_DIR, f"{document_id}_{file.filename}")
    with open(save_path, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)
    chunks = extract_text_from_pdf(save_path)
    add_chunks(document_id, file.filename, chunks)
    return {"success": True, "message": f"Updated. {len(chunks)} chunks re-indexed."}

@app.post("/query")
def query(request: QueryRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured on server. Add OPENROUTER_API_KEY to backend/.env")
    return run_rag_pipeline(request.query, OPENROUTER_API_KEY)

@app.post("/test-guardrail")
def test_guardrail(request: GuardrailTestRequest):
    result = check_input(request.query)
    return {"query": request.query, "safe": result["safe"],
            "threat_type": result.get("threat_type", "NONE"), "reason": result["reason"]}

@app.post("/generate-report")
def create_report(request: ReportRequest):
    report_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
    try:
        generate_report(request.topic, request.answer, request.chunks, output_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    return {"success": True, "report_id": report_id, "download_url": f"/download-report/{report_id}"}

@app.get("/download-report/{report_id}")
def download_report(report_id: str):
    path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(path, media_type="application/pdf", filename=f"research_report_{report_id}.pdf")
