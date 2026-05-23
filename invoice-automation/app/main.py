from fastapi import FastAPI
from .database import engine, ensure_invoice_columns
from .models import Base
from .routes.upload import router as upload_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.include_router(upload_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
ensure_invoice_columns()



@app.get("/")
def home():
    return {"message": "API Running"}