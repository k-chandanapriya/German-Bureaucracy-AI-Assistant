# Architecture

```
 Next.js web app ──HTTP/JSON──► FastAPI backend
                                   │
       ┌───────────────────────────┼──────────────────────────────┐
       │                           │                              │
 Extraction (AI_PROVIDER)     Deadline engine (plain Python)   Outputs
 - image / PDF → JSON schema  - notification fiction           - .ics with VALARMs
 - ollama: local model,       - §§ 187–193 BGB, § 108 AO,       - GiroCode (EPC069-12)
   PDF → page images            § 31 VwVfG, § 26 SGB X          - reply templates (Jinja)
 - anthropic: Sonnet first,
   Opus if confidence < 0.7
 - validators: IBAN checksum, - Bundesland holidays             - DIN 5008 PDF (fpdf2)
   date sanity, uncertainty                                   
       │                           │                              │
       └──────────── Result card (services/analysis.py) ──────────┘
                                   │
                    SQLModel: Case ─< Letter, Case ─< CaseEvent
```

## Principles

1. **The model never computes dates.** It copies the letter date, printed dates and the period from the Rechtsbehelfsbelehrung. `app/deadlines/engine.py` computes and explains the result. The engine has its own unit tests (`tests/test_deadline_engine.py`).
2. **The model never writes legal text.** Reply options come from `app/replies/templates.py`. Each template is fixed German text with fields; the model's extraction only pre-fills fields, which the user can edit.
3. **Conservative by default.** When law or courts disagree we show the earlier date: no weekend shift of the notification day outside tax law, printed payment dates are never moved, and an earlier printed date wins over a computed one.
4. **Flag, don't trust.** IBAN checksum, implausible dates, low model confidence and fields the model marked uncertain all show up as "please confirm with the original letter".

## Deadline rules

| Rule | Source | Implementation |
|---|---|---|
| Letter counts as received on the 4th day after posting (3rd before 2025) | § 122 (2) AO, § 41 (2) VwVfG, § 37 (2) SGB X | `notification_days()` |
| Tax law: deemed receipt on a weekend/holiday moves to the next working day | BFH IX R 68/98 | only for `LegalBasis.AO` |
| Day of the event is not counted; month period ends on the same date | § 187 (1), § 188 (2) BGB | `add_period()` |
| Missing day (31 → February) → last day of month | § 188 (3) BGB | `relativedelta` clamp |
| Last day on Sat/Sun/holiday → next working day | § 193 BGB, § 108 (3) AO, § 31 (3) VwVfG | `roll_forward()` |
| Holidays depend on the state | — | `holidays.Germany(subdiv=…)` |

## Choosing the model

`app/extraction/extractor.py` dispatches on `AI_PROVIDER`. Both readers return the same `LetterExtraction`, so nothing downstream changes.

| | `ollama` (local) | `anthropic` (Claude) |
|---|---|---|
| Cost | free | per token |
| Privacy | letter never leaves the machine | processed by Anthropic under a DPA |
| Input | images only: PDFs rendered with pypdfium2, photos scaled to 1600 px | images and PDFs directly |
| Method | 3 passes: transcribe each page (skipped for digital PDFs, which use their text layer) → extract JSON from the text → regex cross-check of letter date, IBAN, reference numbers, instalments, validity/passport expiry and appeal period against the transcript | one structured-output call |
| Accuracy | good on clean scans, weaker on bad photos; confidence capped at 0.9 | best; low-confidence letters re-read by Opus |
| Speed | ~80–100 s for a one-page letter (`qwen2.5vl:7b`, Apple M4, 24 GB) | a few seconds |

## Data protection

- Letters are processed in memory and only the extraction is stored. Photos are not written to disk.
- Users can delete a case with all its letters (`DELETE /api/cases/{id}`).
- For production: EU hosting (Frankfurt), Postgres with row-level security per user, encryption at rest, a DPA with every processor, and no training on user letters.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/meta` | Bundesländer, letter types, templates, samples |
| POST | `/api/letters/analyze/jobs` | multipart `files[]` + `bundesland` → background job (used by the web app) |
| GET | `/api/jobs/{id}` | job status, current stage, elapsed seconds, result card |
| POST | `/api/letters/analyze` | same, but waits for the result card |
| POST | `/api/letters/sample/{id}` | sample letter without an API key |
| GET | `/api/letters/{id}` | stored result card |
| POST | `/api/letters/{id}/recompute` | user-corrected letter/receipt date |
| GET | `/api/letters/{id}/calendar.ics` | calendar file |
| GET | `/api/letters/{id}/girocode.svg` | payment QR code |
| POST | `/api/deadlines/compute` | standalone deadline calculator |
| GET | `/api/replies/prefill` | suggested field values from a letter |
| POST | `/api/replies/draft` | German + English reply |
| POST | `/api/replies/pdf` | DIN 5008 PDF |
| GET/PATCH/DELETE | `/api/cases[/{id}]` | cases, status, deletion |

Interactive docs: http://localhost:8010/docs
