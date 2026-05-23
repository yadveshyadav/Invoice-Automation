from pathlib import Path


def extract_text_from_pdf(path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text
    except Exception:
        return ""

    try:
        return extract_text(str(path)) or ""
    except Exception:
        return ""
