from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import mimetypes
import re
import shutil
import uuid

from ..database import SessionLocal
from ..models import Invoice
from ..schemas import InvoiceUpdate
from ..services.parser import parse_invoice
from ..services.ocr_services import extract_text
from ..services.pdf_services import extract_text_from_pdf

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp"}
TEXT_EXTENSIONS = {".txt", ".csv", ".md", ".log"}
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf"} | TEXT_EXTENSIONS

FILENAME_SAFE_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def _sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    if not name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    sanitized = FILENAME_SAFE_PATTERN.sub("_", name)
    sanitized = sanitized.strip("._-") or "upload"
    return f"{uuid.uuid4().hex}_{sanitized}"


def _detect_file_type(file_location: Path) -> str:
    suffix = file_location.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix == ".pdf":
        return "pdf"
    if suffix in TEXT_EXTENSIONS:
        return "text"

    mime_type, _ = mimetypes.guess_type(file_location.name)
    if mime_type:
        if mime_type.startswith("image/"):
            return "image"
        if mime_type == "application/pdf":
            return "pdf"
        if mime_type.startswith("text/"):
            return "text"

    try:
        header = file_location.read_bytes(16)
    except Exception:
        return "unknown"

    if header.startswith(b"%PDF-"):
        return "pdf"
    if header.startswith(b"\xff\xd8\xff") or header.startswith(b"\x89PNG\r\n\x1a\n") or header.startswith(b"BM"):
        return "image"
    return "unknown"


def _extract_text_from_file(file_location: Path) -> str:
    file_type = _detect_file_type(file_location)
    if file_type == "image":
        return extract_text(str(file_location))
    if file_type == "pdf":
        return extract_text_from_pdf(file_location)
    if file_type == "text":
        try:
            return file_location.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    # Unknown files may still contain readable plain text
    try:
        return file_location.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        raise HTTPException(status_code=415, detail="Unsupported file type")


@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    filename = _sanitize_filename(file.filename)
    file_location = UPLOAD_DIR / filename

    with file_location.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = _extract_text_from_file(file_location)
    parsed = parse_invoice(text)

    db = SessionLocal()
    invoice = Invoice(
        vendor=parsed.get("vendor", ""),
        invoice_number=parsed.get("invoice_number", ""),
        amount=parsed.get("amount", ""),
        gstin=parsed.get("gstin", ""),
        sgst=parsed.get("sgst", ""),
        cgst=parsed.get("cgst", ""),
        igst=parsed.get("igst", ""),
        date=parsed.get("date", ""),
        status="Processed",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    db.close()

    result = {
        "id": invoice.id,
        "filename": file.filename,
        "vendor": invoice.vendor,
        "invoice_number": invoice.invoice_number,
        "amount": invoice.amount,
        "date": invoice.date,
        "gstin": invoice.gstin,
        "sgst": invoice.sgst,
        "cgst": invoice.cgst,
        "igst": invoice.igst,
        "status": invoice.status,
        "raw_text": text,
        "path": str(file_location),
    }
    return result


@router.get("/invoices")
def list_invoices():
    db = SessionLocal()
    invoices = db.query(Invoice).all()
    db.close()
    return [
        {
            "id": invoice.id,
            "vendor": invoice.vendor,
            "invoice_number": invoice.invoice_number,
            "amount": invoice.amount,
            "date": invoice.date,
            "gstin": invoice.gstin,
            "sgst": invoice.sgst,
            "cgst": invoice.cgst,
            "igst": invoice.igst,
            "status": invoice.status,
        }
        for invoice in invoices
    ]


@router.put("/invoices/{invoice_id}")
def update_invoice(invoice_id: int, update: InvoiceUpdate):
    db = SessionLocal()
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        db.close()
        raise HTTPException(status_code=404, detail="Invoice not found")

    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(invoice, key, value)

    db.commit()
    db.refresh(invoice)
    db.close()

    return {
        "id": invoice.id,
        "vendor": invoice.vendor,
        "invoice_number": invoice.invoice_number,
        "amount": invoice.amount,
        "gstin": invoice.gstin,
        "sgst": invoice.sgst,
        "cgst": invoice.cgst,
        "igst": invoice.igst,
        "date": invoice.date,
    }


@router.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: int):
    db = SessionLocal()
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        db.close()
        raise HTTPException(status_code=404, detail="Invoice not found")

    db.delete(invoice)
    db.commit()
    db.close()

    return {"detail": "Invoice deleted"}
