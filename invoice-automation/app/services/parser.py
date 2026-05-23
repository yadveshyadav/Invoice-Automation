import re
from typing import Dict, List, Pattern



RE_FLAGS = re.IGNORECASE | re.MULTILINE

def _compile(patterns: List[str]) -> List[Pattern]:
    return [re.compile(p, flags=RE_FLAGS) for p in patterns]


def _first_match(compiled_patterns: List[Pattern], text: str) -> str:
    for regex in compiled_patterns:
        m = regex.search(text)
        if m:
            return m.group(1).strip()
    return ""


def _all_matches(compiled_patterns, text: str) -> List[str]:
    values: List[str] = []
    for regex in compiled_patterns:
      
        if isinstance(regex, str):
            regex = re.compile(regex, flags=RE_FLAGS)
        for m in regex.finditer(text):
            if m:
                values.append(m.group(1).strip())
    return values


def _looks_like_amount_line(line: str) -> bool:
    line = line.strip()
    if not line:
        return False

    lower = line.lower()
    ignore_prefixes = [
        'round off',
        'amount chargeable',
        'tax amount',
        'tax amount (in words)',
        'amount chargeable (in words)',
        'invoice',
        'delivery note',
        'reference no',
        "buyer's order", 
        'terms of payment',
        'place of supply',
        'rate',
        'hsn/sac',
        'description of goods',
        'quantity',
        'amount due',
        'balance due',
        'net amount',
        'total',
        'less',
        'consignee',
        'buyer',
        'state name',
        'gstin',
        'dispatch',
        'destination',
        'bank',
        'company',
        'e-invoice',
        'irn',
    ]
    for prefix in ignore_prefixes:
        if lower.startswith(prefix):
            return False
    if re.fullmatch(r"[0-9,]+(?:\.\d{1,2})?", line):
        return True
    if re.search(r"(?:₹|Rs\.?|INR\.? )\s*[0-9,]+(?:\.\d{1,2})?", line):
        return True
   
    if re.search(r"[0-9,]+(?:\.\d{1,2})?%.*[0-9,]+(?:\.\d{1,2})?", line):
        return True
    return False


def _looks_like_label_line(line: str) -> bool:
    lower = line.strip().lower()
    if not lower:
        return True
    label_keywords = [
        'invoice no',
        'e-way',
        'bill no',
        'dated',
        'delivery note',
        'reference no',
        'dispatch doc',
        'terms of payment',
        'mode/terms',
        'destination',
        'place of supply',
        'buyer',
        'consignee',
        'supplier',
        'gstin',
        'state name',
        'ack no',
        'ack date',
        'hsn/sac',
        'quantity',
        'rate',
        'description of goods',
        'tax amount',
        'taxable value',
        'amount chargeable',
        'amount due',
        'total tax',
        'amount',
        'round off',
        'less',
        'e-mail',
        'cin',
        'bank',
        'branch',
        'company',
        'declaration',
    ]
    for keyword in label_keywords:
        if keyword in lower:
            return True
    if lower.endswith(':'):
        return True
    return False


def _looks_like_unit_line(line: str) -> bool:
    lower = line.lower()
    if re.search(r"\b(?:kg|kgs|qty|quantity|nos|pcs|pieces|units|litre|litres|meter|metre|mtr|mt)\b", lower):
        return True
    if re.search(r"\b(?:per|rate|amount|hsn|description)\b", lower) and re.search(r"\d", lower):
        return True
    return False


def _value_after_label(labels, text, must_be_amount: bool = False):
   
    lines = [l.rstrip() for l in text.splitlines()]
    for i, line in enumerate(lines):
        low = line.lower()
        for lbl in labels:
            pattern = rf"(?:^|\W){re.escape(lbl.lower())}(?:$|\W)"
            match = re.search(pattern, low)
            if match:
                # try : 
                if ':' in line:
                    parts = line.split(':', 1)
                    if parts[1].strip():
                        return parts[1].strip()
                # tring same line
                after_label = line[match.end():].strip()
                if after_label and re.search(r"(?:₹|Rs\.?|INR\.?|\d)", after_label):
                    if not _looks_like_unit_line(after_label):
                        return after_label
                # else return
                for j in range(i + 1, min(i + 12, len(lines))):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    if _looks_like_label_line(candidate):
                        continue
                    if _looks_like_unit_line(candidate):
                        continue
                    if must_be_amount and not _looks_like_amount_line(candidate):
                        continue
                    return candidate
    return ""


def _find_amount_after_label(labels, text):
    lines = [l.strip() for l in text.splitlines()]
    for i, line in enumerate(lines):
        low = line.lower()
        for lbl in labels:
            pattern = rf"(?:^|\W){re.escape(lbl.lower())}(?:$|\W)"
            if re.search(pattern, low):
                amount_candidates = []
                for j in range(i + 1, min(i + 20, len(lines))):
                    candidate = lines[j].strip()
                    if not candidate:
                        continue
                    lower = candidate.lower()
                    if lower.startswith((
                        'cgst',
                        'sgst',
                        'sgst/utgst',
                        'rate',
                        'amount',
                        'round off',
                        'tax amount',
                        'total',
                        'less',
                        'invoice',
                        'ack',
                        'irn',
                        'company',
                        'bank',
                        'state name',
                        'gstin',
                        'buyer',
                        'consignee',
                    )):
                        continue
                    if _looks_like_unit_line(candidate):
                        continue
                    if _looks_like_amount_line(candidate):
                        amount_candidates.append(candidate)
                if amount_candidates:
                    
                    for candidate in reversed(amount_candidates):
                        if re.search(r"[₹RsINR]", candidate) or '.' in candidate:
                            return candidate
                    return amount_candidates[-1]
    return ""


def _value_after_label_amount(labels, text):
    """Find a tax label and return the amount value. If the next line is a percent, look further for the actual amount."""
    value = _value_after_label(labels, text, must_be_amount=True)
    if not value:
        return ""

    cleaned = value.strip()
    if "%" in cleaned:
        after_percent = cleaned.split("%", 1)[1]
        after_amount = re.search(r"(?:₹|Rs\.?|INR\.? )?\s*([0-9,]+(?:\.\d{1,2})?)", after_percent)
        if after_amount:
            return after_amount.group(1).strip()

    if not _looks_like_amount_line(cleaned):
        alt = _find_amount_after_label(labels, text)
        if alt:
            return alt

    if re.fullmatch(r"[0-9,]+(?:\.\d{1,2})?%", cleaned):
        lines = [l.strip() for l in text.splitlines()]
        amount_header_index = None
        for k, line in enumerate(lines):
            if re.search(r"\bamount\b", line, flags=re.IGNORECASE):
                amount_header_index = k
                break

        lower_labels = [lbl.lower() for lbl in labels]
        if amount_header_index is not None:
            amount_candidates = []
            for candidate in lines[amount_header_index + 1:]:
                candidate = candidate.strip()
                if not candidate:
                    continue
                if re.search(r"[a-zA-Z]", candidate) and not re.search(r"(?:₹|Rs\.?|INR\.? )", candidate):
                    continue
                amount_matches = re.findall(r"(?:₹|Rs\.?|INR\.? )?\s*([0-9,]+(?:\.\d{1,2})?)", candidate)
                for match in amount_matches:
                    amount_candidates.append(match.strip())
                    if len(amount_candidates) >= 3:
                        break
                if len(amount_candidates) >= 3:
                    break

            if amount_candidates:
                if any("cgst" in lbl for lbl in lower_labels):
                    if len(amount_candidates) >= 2:
                        return amount_candidates[1]
                    return amount_candidates[0]
                if any("sgst" in lbl for lbl in lower_labels):
                    if len(amount_candidates) >= 3:
                        return amount_candidates[2]
                    if len(amount_candidates) >= 2:
                        return amount_candidates[1]
                    return amount_candidates[0]

        for i, line in enumerate(lines):
            low = line.lower()
            for lbl in labels:
                pattern = rf"(?:^|\W){re.escape(lbl.lower())}(?:$|\W)"
                if re.search(pattern, low):
                    for j in range(i + 1, len(lines)):
                        candidate = lines[j].strip()
                        if not candidate:
                            continue
                        amount_match = re.search(r"(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)", candidate)
                        if amount_match:
                            return amount_match.group(1).strip()
                        if re.fullmatch(r"[0-9,]+(?:\.\d{1,2})?", candidate):
                            return candidate
                    return cleaned
    return cleaned


def _vendor_from_gstin(text: str) -> str:
    """When GSTIN is present, return the nearest non-empty line above it (likely vendor name)."""
    lines = [l.rstrip() for l in text.splitlines()]
    for i, line in enumerate(lines):
        if 'gstin' in line.lower():
            
            def _is_noise(s: str) -> bool:
                s2 = s.strip().lower()
                if not s2:
                    return True
              
                if s2.startswith('(') and s2.endswith(')'):
                    return True
                noise_keywords = ['original for recipient', 'duplicate for transporter', 'tax invoice', 'e-invoice', 'ack no', 'ack date']
                for nk in noise_keywords:
                    if nk in s2:
                        return True
                # non-letter
                if len(s2) < 4:
                    return True
                return False

           
            company_re = re.compile(r"(LTD|PVT|PRIVATE|COMPANY|PVT\.|LIMITED)", flags=re.IGNORECASE)
            for j in range(i - 1, max(-1, i - 8), -1):
                if not lines[j].strip():
                    continue
                if 'gstin' in lines[j].lower():
                    continue
                if _is_noise(lines[j]):
                    continue
                if company_re.search(lines[j]):
                    return lines[j].strip()
            
            for j in range(i - 1, max(-1, i - 8), -1):
                if not lines[j].strip():
                    continue
                if _is_noise(lines[j]):
                    continue
                if not re.search(r"\d", lines[j]):
                    return lines[j].strip()
    return ""


def _normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _find_invoice_number(text: str) -> str:
    invoice_patterns = _compile([
        r"(?:invoice|inv|bill)\s*(?:no|number|#)\.?\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-. ]{0,50})",
        r"\b(?:invoice|inv|bill)\s*#\s*([A-Z0-9][A-Z0-9/\-. ]{0,50})",
        r"\bINV\b\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-. ]{0,50})",
    ])
    for regex in invoice_patterns:
        m = regex.search(text)
        if m:
            return m.group(1).strip()

    for line in text.splitlines():
        lower = line.lower()
        if not re.search(r"\b(?:invoice|inv|bill)\b", lower):
            continue
        if ':' in line and re.search(r"\b(?:no|number|#)\b", lower):
            value = line.split(':', 1)[1].strip()
            if value:
                match = re.match(r"[A-Z0-9][A-Z0-9/\-.]*", value, flags=RE_FLAGS)
                if match:
                    return match.group(0).strip()
        match = re.search(r"(?:invoice|inv|bill)\s*(?:no|number|#)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-.]+)", line, flags=RE_FLAGS)
        if match:
            return match.group(1).strip()
    return ""


def _find_date(text: str) -> str:
    date_patterns = _compile([
        r"Invoice\s*Date\s*[:\n]?\s*([0-9]{1,2}[-/][A-Za-z]{3,9}[-/][0-9]{2,4})",
        r"Invoice\s*Date\s*[:\n]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})",
        r"Dated\s*[:\n]?\s*([0-9]{1,2}[-/][A-Za-z]{3,9}[-/][0-9]{2,4})",
        r"Dated\s*[:\n]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})",
        r"(\d{1,2}[-/][A-Za-z]{3,9}[-/][0-9]{2,4})",
        r"(\d{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})",
    ])
    return _first_match(date_patterns, text)
def _find_gstin(text):
   
    pattern = re.compile(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]{3})\b", flags=RE_FLAGS)
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None
        
        

def _find_amount_from_labels(text: str) -> str:
    labels = [
        'Grand Total',
        'Total Amount',
        'Invoice Total',
        'Amount Due',
        'Balance Due',
        'Amount Payable',
        'Net Amount',
        'Amount Chargeable',
        'Total',
    ]
    for line in text.splitlines():
        low = line.lower()
        for lbl in labels:
            if lbl.lower() in low and 'tax' not in low:
                m = re.search(r"([0-9,]+(?:\.\d{1,2})?)", line)
                if m:
                    return m.group(1)
                if ':' in line:
                    parts = line.split(':', 1)
                    if parts[1].strip():
                        value = re.search(r"([0-9,]+(?:\.\d{1,2})?)", parts[1])
                        if value:
                            return value.group(1)
    return ""


def parse_invoice(text: str) -> Dict[str, str]:
    """Extract common invoice fields from raw text.

    Returns keys: vendor, invoice_number, date, total_amount, taxable_value, total_tax
    """

    if not text:
        return {
            "vendor": "",
            "invoice_number": "",
            "gstin_number": "",
            "date": "",
            "total_amount": "",
            "taxable_value": "",
            "total_tax": "",
            "igst": "",
        }

   
    vendor_patterns = _compile([
        r"^([A-Z0-9 &\.-]{4,})\n.*GSTIN",
        r"^([A-Z][A-Z0-9 &\.-]{3,})\n",
    ])
    gstin_patterns = _compile([
        r'GSTIN',
        r'GSTIN/UIN'])

    gstin = _find_gstin(text) or _value_after_label([
        'GSTIN', 'GSTIN/UIN'],
        text,
    )

    invoice_number = _value_after_label(
        ['Invoice No', 'Invoice No.', 'Invoice Number', 'Bill No', 'Bill Number', 'Invoice #', 'Inv No', 'INV', 'Invoice #'],
        text,
    ) or _find_invoice_number(text)

    date = _value_after_label(['Invoice Date', 'Dated', 'Date', 'Date of Invoice'], text) or _find_date(text)

  
    total_patterns = _compile([
        r"(?:Grand\s*Total|Total\s*Amount|Invoice\s*Total|Total\s*Payable|Amount\s*Due|Balance\s*Due|Amount\s*Payable|Net\s*Amount|Amount\s*Chargeable|Total|Ammount)\s*(?:is|[:\-])?\s*[\n\r\s]*(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"(?:Grand\s*Total|Total\s*Amount|Invoice\s*Total|Total\s*Payable|Amount\s*Due|Balance\s*Due|Amount\s*Payable|Net\s*Amount|Amount\s*Chargeable|Total|Ammount)[ \t]*(?:is|[:\-])?[ \t]*([0-9,]+(?:\.\d{1,2})?)",
    ])

    taxable_patterns = _compile([
        r"Taxable\s*Value\s*[:\n\s]*([0-9,]+(?:\.\d{1,2})?)",
        r"Taxable\s*Value\s*([0-9,]+(?:\.\d{1,2})?)",
    ])

    total_tax_patterns = _compile([
        r"Total\s*Tax\s*Amount\s*[:\n\s]*([0-9,]+(?:\.\d{1,2})?)",
        r"Total\s*Tax Amount\s*[:\n\s]*([0-9,]+(?:\.\d{1,2})?)",
        r"Total\s*Tax\s*[:\n\s]*([0-9,]+(?:\.\d{1,2})?)",
    ])

   
    vendor = (
        _vendor_from_gstin(text)
        or _value_after_label(['Vendor', 'Supplier', 'Billed To', 'Bill To', 'From', 'GSTIN', 'GSTIN/UIN', 'E-Mail', 'CIN'], text)
        or _first_match(vendor_patterns, text)
    )

    # Amounts
    totals = _all_matches(total_patterns, text)
    if not totals:
        label_amount = _value_after_label(
            [
                'Grand Total',
                'Total Amount',
                'Invoice Total',
                'Ammount',
                'Amount Due',
                'Balance Due',
                'Amount Chargeable',
                'Net Amount',
                'Total',
            ],
            text,
            must_be_amount=True,
        )
        if label_amount:
            totals = [label_amount]

    if not totals:
        label_amount = _find_amount_from_labels(text)
        if label_amount:
            totals = [label_amount]

    if not totals:
        totals = _all_matches(_compile([r"(?:(?:₹|Rs\.?|INR\.? )\s*)([0-9,]+(?:\.\d{1,2})?)"]), text)
        if totals:
            totals = [totals[-1]]

    def _score_amount(value: str) -> float:
        cleaned = re.sub(r"[^0-9.]", "", value)
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    best_amount = ""
    best_value = 0.0
    for amount_candidate in totals:
        score = _score_amount(amount_candidate)
        if score > best_value:
            best_value = score
            best_amount = amount_candidate

    total_amount = best_amount

    if not vendor:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if lines:
            vendor = lines[0]

    taxable_value = _first_match(taxable_patterns, text) or _value_after_label(['Taxable Value'], text, must_be_amount=True)
    total_tax = _first_match(total_tax_patterns, text) or _value_after_label(['Total Tax', 'Total Tax Amount', 'Total Tax Amount'], text, must_be_amount=True)

    
    sgst_patterns = _compile([
        r"SGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*|[0-9]+(?:\.\d{1,2})?\s*%)?\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"SGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*|[0-9]+(?:\.\d{1,2})?\s*%)?\s*(?:[:\n]\s*)?([0-9,]+(?:\.\d{1,2})?)(?!%)",
        r"SGST\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"SGST\s*(?:[:\n]\s*)*([0-9,]+(?:\.\d{1,2})?)(?!%)",
        r"S\s*G\s*S\s*T\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*)?\s*(?:[:\n]\s*)?([0-9]+(?:\.\d{1,2})?\s*%)",
        r"SGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*)?\s*(?:[:\n]\s*)?([0-9]+(?:\.\d{1,2})?\s*%)",
        r"State\s*GST(?:\s*Amount)?\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"State\s*GST(?:\s*Amount)?\s*(?:[:\n]\s*)*([0-9,]+(?:\.\d{1,2})?)(?!%)"
    ])
    cgst_patterns = _compile([
        r"CGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*|[0-9]+(?:\.\d{1,2})?\s*%)?\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"CGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*|[0-9]+(?:\.\d{1,2})?\s*%)?\s*(?:[:\n]\s*)?([0-9,]+(?:\.\d{1,2})?)(?!%)",
        r"CGST\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"CGST\s*(?:[:\n]\s*)*([0-9,]+(?:\.\d{1,2})?)(?!%)",
        r"C\s*G\s*S\s*T\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*)?\s*(?:[:\n]\s*)?([0-9]+(?:\.\d{1,2})?\s*%)",
        r"CGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*)?\s*(?:[:\n]\s*)?([0-9]+(?:\.\d{1,2})?\s*%)",
        r"Central\s*GST(?:\s*Amount)?\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"Central\s*GST(?:\s*Amount)?\s*(?:[:\n]\s*)*([0-9,]+(?:\.\d{1,2})?)(?!%)"
    ])
    igst_patterns = _compile([
        r"IGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*|[0-9]+(?:\.\d{1,2})?\s*%)?\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"IGST\s*(?:Amount|Amt)?\s*(?:@[^₹\n]*|[0-9]+(?:\.\d{1,2})?\s*%)?\s*(?:[:\n]\s*)?([0-9,]+(?:\.\d{1,2})?)(?!%)",
        r"IGST\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"IGST\s*(?:[:\n]\s*)*([0-9,]+(?:\.\d{1,2})?)(?!%)",
        r"Integrated\s*GST(?:\s*Amount)?\s*(?:[:\n]\s*)?(?:₹|Rs\.?|INR\.? )\s*([0-9,]+(?:\.\d{1,2})?)",
        r"Integrated\s*GST(?:\s*Amount)?\s*(?:[:\n]\s*)*([0-9,]+(?:\.\d{1,2})?)(?!%)"
    ])
    sgst = _value_after_label_amount([
        'SGST Output', 'SGST Amount', 'SGST Amt', 'SGST', 'S G S T', 'State GST', 'State GST Amount', 'SGST Charge'
    ], text) or _first_match(sgst_patterns, text) or ""
    cgst = _value_after_label_amount([
        'CGST Output', 'CGST Amount', 'CGST Amt', 'CGST', 'C G S T', 'Central GST', 'Central GST Amount', 'CGST Charge'
    ], text) or _first_match(cgst_patterns, text) or ""
    igst = _value_after_label_amount([
        'IGST Output', 'IGST Amount', 'IGST Amt', 'IGST', 'Integrated GST', 'Integrated GST Amount', 'IGST Charge'
    ], text) or _first_match(igst_patterns, text) or ""

   
    def _norm_amt(a: str) -> str:
        return re.sub(r"[^0-9.]", "", a).strip()

    def _norm_tax_amt(a: str) -> str:
        cleaned = a.strip()
        if cleaned.endswith("%"):
            return re.sub(r"[^0-9.%]", "", cleaned).strip()
        return _norm_amt(cleaned)

    norm_total = _norm_amt(total_amount)
    return {
        "vendor": vendor,
        "invoice_number": invoice_number,
        "date": date,
        "gstin": gstin,
        "sgst": _norm_tax_amt(sgst),
        "cgst": _norm_tax_amt(cgst),
        "igst": _norm_tax_amt(igst),
        "total_amount": norm_total,
        "amount": norm_total,  
        "taxable_value": _norm_amt(taxable_value),
        "total_tax": _norm_amt(total_tax),
    }