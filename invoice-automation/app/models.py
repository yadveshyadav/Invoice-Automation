from sqlalchemy import Column, Integer, String
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    vendor = Column(String)
    invoice_number = Column(String, index=True)
    amount = Column(String)
    date = Column(String)
    gstin = Column(String)
    sgst = Column(String)
    cgst = Column(String)
    igst = Column(String)
    status = Column(String, default="Processed")
