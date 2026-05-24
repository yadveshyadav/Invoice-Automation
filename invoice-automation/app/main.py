import sys
from pathlib import Path


app_dir = Path(__file__).resolve().parent
repo_root = app_dir.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.database import engine, ensure_invoice_columns
from app.models import Base
from app.routes.upload import router as upload_router

frontend_build_dir = app_dir / "frontend" / "build"

app = FastAPI()
app.include_router(upload_router, prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
ensure_invoice_columns()


@app.get("/api")
def api_root():
    return {"message": "API Running"}


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="Not found")

    if frontend_build_dir.exists():
        file_path = frontend_build_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)

        index_file = frontend_build_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend not available")
