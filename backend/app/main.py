"""Briefly API: understand German official letters, compute deadlines, draft replies."""

from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime, timedelta, timezone

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings
from app import jobs, limits
from app.db import CASE_STATUSES, Case, CaseEvent, Letter, engine, get_session, init_db
from app.deadlines.engine import (
    BUNDESLAENDER,
    DeadlineInput,
    Delivery,
    LegalBasis,
    PeriodUnit,
    compute_deadline,
)
from app.extraction.errors import ExtractionError
from app.extraction.extractor import extract_letter
from app.extraction.samples import SAMPLES, sample_extraction
from app.extraction.schemas import LetterExtraction
from app.knowledge.glossary import GLOSSARY
from app.knowledge.taxonomy import LETTER_TYPES, SENDERS
from app.replies.letter_pdf import render_letter_pdf
from app.replies.templates import REPLY_TEMPLATES, TemplateFieldError, render_reply
from app.services.analysis import build_card
from app.services.calendar_ics import build_ics
from app.services.girocode import epc_payload, girocode_svg

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Briefly – German Bureaucracy AI Assistant", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

FOLLOW_UP_AFTER = timedelta(weeks=6)


def owner_id(x_briefly_owner: str | None = Header(None)) -> str:
    """Each browser sends a random id; cases are only visible to the browser that made them."""
    if not x_briefly_owner or not re.fullmatch(r"[A-Za-z0-9-]{16,64}", x_briefly_owner):
        raise HTTPException(401, "Missing browser id. Reload the page and try again.")
    return x_briefly_owner


def _take_read(request: Request) -> None:
    try:
        limits.take(request.client.host if request.client else "unknown")
    except limits.LimitReached as e:
        raise HTTPException(429, str(e)) from e


def _check_land(bundesland: str) -> str:
    code = bundesland.upper()
    if code not in BUNDESLAENDER:
        raise HTTPException(422, f"Unknown Bundesland '{bundesland}'")
    return code


# --------------------------------------------------------------------- meta
@app.get("/api/health")
def health() -> dict:
    # Render sets RENDER_GIT_COMMIT, which shows which version is running.
    return {"status": "ok", "version": os.environ.get("RENDER_GIT_COMMIT", "local")[:7]}


# Official product names for the model ids we ship with, shown to users.
MODEL_NAMES = {
    "qwen2.5vl:7b": "Qwen2.5-VL 7B by Alibaba Cloud",
    "qwen/qwen3.8-27b": "Qwen3.8 27B by Alibaba Cloud",
    "claude-sonnet-5-5": "Claude Sonnet 5.5 by Anthropic",
    "claude-opus-5-5": "Claude Opus 5.5 by Anthropic",
}


@app.get("/api/meta")
def meta() -> dict:
    model = {"ollama": settings.ollama_model, "groq": settings.groq_model}.get(settings.ai_provider, settings.extraction_model)
    return {
        "bundeslaender": BUNDESLAENDER,
        "default_bundesland": settings.default_bundesland,
        "senders": SENDERS,
        "letter_types": [t.to_dict() for t in LETTER_TYPES.values()],
        "reply_templates": [t.to_dict() for t in REPLY_TEMPLATES.values()],
        "samples": [{"id": k, "label": v["label"], "preview": v["preview"]} for k, v in SAMPLES.items()],
        "case_statuses": CASE_STATUSES,
        "ai_provider": settings.ai_provider,
        "ai_model": model,
        "ai_model_name": MODEL_NAMES.get(model, model),
    }


@app.get("/api/glossary")
def glossary() -> dict:
    return GLOSSARY


# ----------------------------------------------------------------- letters
def _store(session: Session, ex: LetterExtraction, card: dict, bundesland: str, model: str, owner: str) -> dict:
    """Attach the letter to an existing case with the same reference number, or open a new case."""
    refs = [r.value.replace(" ", "") for r in ex.reference_numbers]
    case = None
    if refs:
        case = session.exec(select(Case).where(Case.owner == owner, Case.reference.in_(refs))).first()  # type: ignore[union-attr]

    is_new_case = case is None
    if case is None:
        case = Case(
            owner=owner,
            title=ex.title,
            sender_name=ex.sender_name,
            sender_category=ex.sender_category,
            reference=refs[0] if refs else None,
            status="action_needed" if card["severity"] != "info" else "understood",
        )
        session.add(case)
        session.flush()
    else:
        case.status = "action_needed" if card["severity"] != "info" else case.status
        case.updated_at = datetime.now(timezone.utc)

    letter = Letter(
        case_id=case.id,
        letter_type=ex.letter_type,
        title=ex.title,
        letter_date=ex.letter_date,
        bundesland=bundesland,
        model=model,
        extraction=ex.model_dump(),
        card=card,
    )
    session.add(letter)
    session.add(CaseEvent(case_id=case.id, kind="letter_received", text=f"Letter: {ex.title}"))
    session.commit()
    session.refresh(letter)
    return {"letter_id": letter.id, "case_id": case.id, "linked_to_existing_case": not is_new_case, **card}


async def _read_uploads(files: list[UploadFile]) -> list[tuple[bytes, str]]:
    payload: list[tuple[bytes, str]] = []
    total = 0
    for f in files:
        data = await f.read()
        total += len(data)
        payload.append((data, f.content_type or "application/octet-stream"))
    if total > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Upload is larger than {settings.max_upload_mb} MB")
    return payload


def _read_and_store(payload: list[tuple[bytes, str]], land: str, owner: str, progress=lambda _: None) -> dict:
    ex, model = extract_letter(payload, progress)
    progress("Calculating deadlines")
    card = build_card(ex, land)
    with Session(engine) as session:
        return _store(session, ex, card, land, model, owner)


@app.post("/api/letters/analyze")
async def analyze_letter(
    request: Request,
    files: list[UploadFile] = File(...),
    bundesland: str = Form(settings.default_bundesland),
    owner: str = Depends(owner_id),
) -> dict:
    """Read a letter and wait for the result (simple API clients)."""
    land = _check_land(bundesland)
    payload = await _read_uploads(files)
    _take_read(request)
    try:
        # Model calls block, so run them off the event loop.
        return await run_in_threadpool(_read_and_store, payload, land, owner)
    except ExtractionError as e:
        raise HTTPException(502, str(e)) from e


@app.post("/api/letters/analyze/jobs", status_code=202)
async def start_reading_job(
    request: Request,
    files: list[UploadFile] = File(...),
    bundesland: str = Form(settings.default_bundesland),
    owner: str = Depends(owner_id),
) -> dict:
    """Start reading a letter in the background; poll GET /api/jobs/{id} for progress."""
    land = _check_land(bundesland)
    payload = await _read_uploads(files)
    _take_read(request)
    job = jobs.submit(lambda progress: _read_and_store(payload, land, owner, progress), ExtractionError, owner)
    return job.to_dict()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, owner: str = Depends(owner_id)) -> dict:
    job = jobs.get(job_id)
    if not job or job.owner != owner:
        raise HTTPException(404, "Job not found (the backend may have restarted). Please upload the letter again.")
    return job.to_dict()


@app.post("/api/letters/sample/{sample_id}")
def analyze_sample(
    sample_id: str,
    bundesland: str = settings.default_bundesland,
    session: Session = Depends(get_session),
    owner: str = Depends(owner_id),
) -> dict:
    land = _check_land(bundesland)
    try:
        ex = sample_extraction(sample_id)
    except KeyError as e:
        raise HTTPException(404, "Unknown sample") from e
    card = build_card(ex, land)
    return _store(session, ex, card, land, "sample", owner)


def _get_case(session: Session, case_id: int, owner: str) -> Case:
    case = session.get(Case, case_id)
    if not case or case.owner != owner:
        raise HTTPException(404, "Case not found")
    return case


def _get_letter(session: Session, letter_id: int, owner: str) -> Letter:
    letter = session.get(Letter, letter_id)
    case = session.get(Case, letter.case_id) if letter else None
    if not letter or not case or case.owner != owner:
        raise HTTPException(404, "Letter not found")
    return letter


@app.get("/api/letters/{letter_id}")
def get_letter(letter_id: int, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> dict:
    letter = _get_letter(session, letter_id, owner)
    return {"letter_id": letter.id, "case_id": letter.case_id, **letter.card}


class Correction(BaseModel):
    letter_date: str | None = None
    received_date: str | None = None
    bundesland: str | None = None


@app.post("/api/letters/{letter_id}/recompute")
def recompute(letter_id: int, body: Correction, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> dict:
    """User confirms or corrects the critical fields; deadlines are recomputed."""
    letter = _get_letter(session, letter_id, owner)
    ex = LetterExtraction.model_validate(letter.extraction)
    if body.letter_date:
        ex.letter_date = body.letter_date
    land = _check_land(body.bundesland or letter.bundesland)
    received = date.fromisoformat(body.received_date) if body.received_date else None
    card = build_card(ex, land, received)
    letter.extraction, letter.card, letter.bundesland = ex.model_dump(), card, land
    session.add(letter)
    session.commit()
    return {"letter_id": letter.id, "case_id": letter.case_id, **card}


@app.get("/api/letters/{letter_id}/calendar.ics")
def letter_calendar(letter_id: int, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> Response:
    letter = _get_letter(session, letter_id, owner)
    card = letter.card
    refs = ", ".join(f"{r['label']} {r['value']}" for r in card["reference_numbers"])
    events = [
        {
            "title": f"{d['label']} – {card['sender']['name']}",
            "date": date.fromisoformat(d["due_date"]),
            "description": f"{card['title']}\n{refs}\n\nHow we calculated it:\n" + "\n".join(d["steps"]),
        }
        for d in card["deadlines"]
    ]
    if not events:
        raise HTTPException(404, "This letter has no deadlines")
    return Response(
        build_ics(events),
        media_type="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="briefly-letter-{letter_id}.ics"'},
    )


@app.get("/api/letters/{letter_id}/girocode.svg")
def letter_girocode(letter_id: int, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> Response:
    pay = _get_letter(session, letter_id, owner).card.get("payment")
    if not pay or not pay.get("iban_valid"):
        raise HTTPException(404, "No valid payment details on this letter")
    payload = epc_payload(pay["recipient"], pay["iban"], pay.get("amount_eur"), pay.get("reference") or "", pay.get("bic") or "")
    return Response(girocode_svg(payload), media_type="image/svg+xml")


# --------------------------------------------------------------- deadlines
class DeadlineRequest(BaseModel):
    bundesland: str
    letter_date: date | None = None
    legal_basis: LegalBasis = LegalBasis.VWVFG
    delivery: Delivery = Delivery.POST
    received_date: date | None = None
    period_length: int | None = None
    period_unit: PeriodUnit | None = None
    explicit_due_date: date | None = None
    label: str = "Deadline"


@app.post("/api/deadlines/compute")
def deadline_calculator(req: DeadlineRequest) -> dict:
    data = req.model_dump()
    data["bundesland"] = _check_land(req.bundesland)
    try:
        return compute_deadline(DeadlineInput(**data)).to_dict()
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


# ----------------------------------------------------------------- replies
class DraftRequest(BaseModel):
    template_id: str
    values: dict[str, str] = {}
    letter_id: int | None = None


@app.get("/api/replies/prefill")
def prefill(template_id: str, letter_id: int, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> dict:
    """Suggested field values taken from the letter (the user can edit them)."""
    if template_id not in REPLY_TEMPLATES:
        raise HTTPException(404, "Unknown template")
    letter = _get_letter(session, letter_id, owner)
    ex = LetterExtraction.model_validate(letter.extraction)
    values: dict[str, str] = {}
    if ex.reference_numbers:
        values["reference"] = ex.reference_numbers[0].value
    if ex.letter_date:
        values["letter_date"] = date.fromisoformat(ex.letter_date).strftime("%d.%m.%Y")
    payable = [a for a in ex.amounts if a.direction == "you_pay"]
    if payable:
        values["amount"] = f"{payable[-1].amount_eur:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    lt = LETTER_TYPES.get(ex.letter_type)
    if lt:
        values["decision_name"] = lt.name_de + (f" {ex.title[-4:]}" if ex.title[-4:].isdigit() else "")
    for d in letter.card.get("deadlines", []):
        values.setdefault("current_deadline", date.fromisoformat(d["due_date"]).strftime("%d.%m.%Y"))
    keys = {f.name for f in REPLY_TEMPLATES[template_id].fields}
    return {k: v for k, v in values.items() if k in keys}


@app.post("/api/replies/draft")
def draft_reply(req: DraftRequest, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> dict:
    try:
        result = render_reply(req.template_id, req.values)
    except KeyError as e:
        raise HTTPException(404, "Unknown template") from e
    except TemplateFieldError as e:
        raise HTTPException(422, str(e)) from e
    if req.letter_id:
        letter = session.get(Letter, req.letter_id)
        case = session.get(Case, letter.case_id) if letter else None
        if letter and case and case.owner == owner:
            session.add(CaseEvent(case_id=letter.case_id, kind="reply_drafted", text=f"Drafted: {REPLY_TEMPLATES[req.template_id].title_en}"))
            session.commit()
    return result


class PdfRequest(BaseModel):
    subject_de: str
    body_de: str
    sender_name: str
    sender_address: str
    recipient_address: str
    city: str


@app.post("/api/replies/pdf")
def reply_pdf(req: PdfRequest) -> Response:
    data = req.model_dump()
    pdf = render_letter_pdf(subject=data.pop("subject_de"), body=data.pop("body_de"), **data)
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="antwort.pdf"'})


# ------------------------------------------------------------------- cases
def _case_dict(case: Case, session: Session, full: bool = False) -> dict:
    letters = session.exec(select(Letter).where(Letter.case_id == case.id).order_by(Letter.created_at)).all()
    deadlines = [d for lt in letters for d in lt.card.get("deadlines", [])]
    upcoming = sorted((d for d in deadlines if d["due_date"] >= date.today().isoformat()), key=lambda d: d["due_date"])
    updated = case.updated_at if case.updated_at.tzinfo else case.updated_at.replace(tzinfo=timezone.utc)
    out = {
        "id": case.id,
        "title": case.title,
        "sender_name": case.sender_name,
        "sender_category": case.sender_category,
        "reference": case.reference,
        "status": case.status,
        "updated_at": case.updated_at.isoformat(),
        "letter_count": len(letters),
        "next_deadline": upcoming[0] if upcoming else None,
        "needs_follow_up": case.status == "waiting" and datetime.now(timezone.utc) - updated > FOLLOW_UP_AFTER,
    }
    if full:
        events = session.exec(select(CaseEvent).where(CaseEvent.case_id == case.id).order_by(CaseEvent.created_at)).all()
        out["letters"] = [
            {"id": lt.id, "title": lt.title, "letter_date": lt.letter_date, "severity": lt.card.get("severity"), "created_at": lt.created_at.isoformat()}
            for lt in letters
        ]
        out["timeline"] = [{"kind": e.kind, "text": e.text, "at": e.created_at.isoformat()} for e in events]
    return out


@app.get("/api/cases")
def list_cases(session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> list[dict]:
    if settings.adopt_unowned_cases:
        for old in session.exec(select(Case).where(Case.owner.is_(None))).all():  # type: ignore[union-attr]
            old.owner = owner
            session.add(old)
        session.commit()
    cases = session.exec(select(Case).where(Case.owner == owner).order_by(Case.updated_at.desc())).all()  # type: ignore[attr-defined]
    return [_case_dict(c, session) for c in cases]


@app.get("/api/cases/{case_id}")
def get_case(case_id: int, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> dict:
    case = _get_case(session, case_id, owner)
    return _case_dict(case, session, full=True)


class StatusUpdate(BaseModel):
    status: str


@app.patch("/api/cases/{case_id}")
def update_case(case_id: int, body: StatusUpdate, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> dict:
    case = _get_case(session, case_id, owner)
    if body.status not in CASE_STATUSES:
        raise HTTPException(422, f"Status must be one of {CASE_STATUSES}")
    case.status = body.status
    case.updated_at = datetime.now(timezone.utc)
    session.add(case)
    session.add(CaseEvent(case_id=case.id, kind="status_changed", text=f"Status → {body.status.replace('_', ' ')}"))
    session.commit()
    return _case_dict(case, session, full=True)


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: int, session: Session = Depends(get_session), owner: str = Depends(owner_id)) -> dict:
    """Data minimisation: users can delete a case and every letter in it."""
    case = _get_case(session, case_id, owner)
    for model in (Letter, CaseEvent):
        for row in session.exec(select(model).where(model.case_id == case_id)).all():
            session.delete(row)
    session.delete(case)
    session.commit()
    return {"deleted": case_id}
