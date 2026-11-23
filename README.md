# Amtspost: German Bureaucracy AI Assistant

Take a photo of an official German letter. Amtspost tells you **what it is, what you have to do and by when**. It puts the deadline in your calendar, drafts the German reply and keeps every letter of a case together.

> Built for the ~14 million foreign nationals in Germany who get letters from the Finanzamt, the Ausländerbehörde and the Beitragsservice and have to work out "one month after notification" on their own.

## What it does

| Step | How |
|---|---|
| **Capture** | Upload photos (several pages) or a PDF |
| **Understand** | A vision model reads the letter into a strict JSON schema: sender, letter type, reference numbers, amounts, IBAN, printed dates, appeal period. Choose a **local model via Ollama** (free, nothing leaves your computer) or **Claude** (best accuracy) |
| **Explain** | Plain English at three depths: *In short → Details → Line by line*, plus "if you do nothing" and an Amtsdeutsch glossary |
| **Deadlines** | A **deterministic engine** (plain Python, not the LLM) applies the 4-day notification rule, §§ 187–193 BGB / § 108 AO / § 31 VwVfG, month ends, weekends and **state-specific holidays**, and shows each step |
| **Act** | `.ics` calendar file with reminders 7, 3 and 1 day before; GiroCode QR for banking apps; reviewed German reply templates with an English back-translation, exported as a DIN 5008 PDF |
| **Track** | Letters with the same Steuernummer / Aktenzeichen / Beitragsnummer are grouped into a case with a timeline and status. After 6 weeks of waiting it suggests a Sachstandsanfrage |

v1 covers **3 senders and 19 letter types** (Finanzamt, Ausländerbehörde, Beitragsservice) and **13 reply templates**.

Example deadline with its reasoning:

```
Letter dated Mon 1 Dec 2025 + 4 days (§ 122 (2) AO, 4-day rule since 2025) = deemed received Fri 5 Dec 2025
Fri 5 Dec 2025 + 1 month = Mon 5 Jan 2026
Deadline: Mon 5 Jan 2026, end of day (24:00)
```

## Tech stack

- **Frontend:** Next.js 16 (App Router, TypeScript, Tailwind CSS 4)
- **Backend:** Python 3.12+, FastAPI, SQLModel (SQLite locally, Postgres in production)
- **AI (pick one in `backend/.env`):**
  - `AI_PROVIDER=ollama`: local vision model (default `qwen2.5vl:7b`) via [Ollama](https://ollama.com); PDFs are rendered to page images with `pypdfium2`
  - `AI_PROVIDER=anthropic`: Claude Sonnet 5.5 with structured output; low-confidence letters are re-read by Claude Opus 5.5
- **Deadlines:** `holidays` (per-Bundesland public holidays) + `python-dateutil`
- **Outputs:** `fpdf2` (DIN 5008 letters), `segno` (EPC GiroCode), hand-written RFC 5545 `.ics`

## Run it locally

You need Python 3.12+ and Node.js 20+.

**1. AI model.** Either run a local model (free and private):

```bash
brew install ollama
ollama serve                 # or open the Ollama app
ollama pull qwen2.5vl:7b     # ~6 GB, needs about 8 GB of free RAM
```

or set `AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in `backend/.env`.

**2. Backend** (http://localhost:8010)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env        # AI_PROVIDER=ollama by default
.venv/bin/uvicorn app.main:app --reload --port 8010
```

**3. Frontend** (http://localhost:3000)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Without any AI model you can still use the deadline calculator and the glossary; the fictional sample letters are available through the API (`POST /api/letters/sample/{id}`, see http://localhost:8010/docs).

**Tests**

```bash
cd backend && .venv/bin/python -m pytest
cd frontend && npm run lint && npm run build
```

## Project layout

```
backend/
  app/
    deadlines/engine.py        deterministic deadline engine (no AI)
    extraction/                Claude vision extractor, schema, validators, sample letters
    knowledge/                 letter-type taxonomy, glossary
    replies/                   German reply templates + DIN 5008 PDF
    services/                  result card, .ics calendar, GiroCode
    db.py, main.py             persistence and REST API
  tests/
frontend/
  app/                         pages: scan, letter result, cases, deadline calculator, glossary
  components/                  result card, deadline list, reply drafter …
docs/
  ARCHITECTURE.md, LEGAL.md
```

## Important

Amtspost gives **information, not legal or tax advice** (Rechtsdienstleistungsgesetz, Steuerberatungsgesetz). It explains, translates, computes deadlines and offers templates the user chooses. Always check dates and amounts against the original letter. See [docs/LEGAL.md](docs/LEGAL.md).

## Roadmap

- [x] Upload → classify → explain → deadline → `.ics` (3 senders, 19 letter types)
- [x] Reply templates + DIN 5008 PDF, case timeline
- [ ] OCR cross-check of amounts/IBAN (PaddleOCR)
- [ ] Google / Outlook calendar sync, push reminders
- [ ] Official PDF form filling (Beitragsservice, ABH forms per city)
- [ ] Mobile app (Expo) with document scanner
- [ ] More senders: Krankenkasse, Familienkasse, Jobcenter, Bußgeldbescheid
