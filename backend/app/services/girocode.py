"""EPC069-12 'GiroCode' QR codes that German banking apps can scan."""

from __future__ import annotations

import io
import re

import segno


def epc_payload(name: str, iban: str, amount_eur: float | None, reference: str = "", bic: str = "") -> str:
    iban = re.sub(r"\s+", "", iban).upper()
    if amount_eur is not None and not (0.01 <= amount_eur <= 999_999_999.99):
        raise ValueError("Amount out of range for a GiroCode")
    lines = [
        "BCD",  # service tag
        "002",  # version (BIC optional inside the EEA)
        "1",  # character set: UTF-8
        "SCT",  # SEPA credit transfer
        (bic or "").strip(),
        name.strip()[:70],
        iban,
        f"EUR{amount_eur:.2f}" if amount_eur else "",
        "",  # purpose code
        "",  # structured creditor reference
        (reference or "").strip()[:140],  # unstructured remittance information
    ]
    return "\n".join(lines)


def girocode_svg(payload: str) -> str:
    qr = segno.make(payload, error="m", encoding="utf-8")
    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=5, border=2, xmldecl=False)
    return buf.getvalue().decode("utf-8")
