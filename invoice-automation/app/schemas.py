from pydantic import BaseModel
from typing import Optional


class InvoiceUpdate(BaseModel):
    vendor: Optional[str] = None
    invoice_number: Optional[str] = None
    amount: Optional[str] = None
    date: Optional[str] = None
    gstin: Optional[str] = None
    sgst: Optional[str] = None
    cgst: Optional[str] = None
    igst: Optional[str] = None