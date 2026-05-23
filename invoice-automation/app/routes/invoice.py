from fastapi import APIRouter
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Invoice

router = APIRouter()

@router.get("/invoices")
def get_invoices():

    db: Session = SessionLocal()

    invoices = db.query(Invoice).all()

    return invoices