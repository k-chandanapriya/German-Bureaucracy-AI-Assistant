# Briefly

Your German letters, briefly.

If you live in Germany and don't read German well, you know the feeling. A letter arrives from the Finanzamt, the Ausländerbehörde or the Beitragsservice, it's two pages of Amtsdeutsch, and somewhere in there is a deadline you really shouldn't miss.

Briefly helps with that. You take a photo of the letter (or upload the PDF) and it tells you what the letter is, what you need to do, and by when. It can put the deadline in your calendar, draft a reply in German, and keep all the letters about the same matter together.

## What it can do

1. Read the letter. You can upload a few photos or a PDF. A vision model picks out the sender, the type of letter, reference numbers, amounts, the IBAN, the date on the letter and the appeal period.
2. Explain it in plain English. There's a short summary, a longer explanation and a line by line translation. It also tells you what happens if you ignore the letter, and there's a small glossary for the typical Amtsdeutsch words.
3. Work out the real deadline. This part doesn't use AI at all. It's plain Python that follows the actual rules: the letter counts as delivered four days after it was posted, then the appeal period is added, and if the last day falls on a weekend or a public holiday in your state, it moves to the next working day. You can see every step of the calculation, so you don't have to trust it blindly.
4. Help you act. You get a calendar file with reminders a week, three days and one day before the deadline, a GiroCode you can scan with your banking app if you have to pay something, and reply templates in German with an English translation next to them. Replies can be downloaded as a proper German letter (DIN 5008) in PDF.
5. Keep track. Letters with the same tax number, file number or contribution number end up in one case, with a timeline and a status. If you've been waiting on an answer for six weeks, it suggests sending a status inquiry.

Right now it knows three senders (Finanzamt, Ausländerbehörde and Beitragsservice), 19 kinds of letters and 13 reply templates.

Here's an example of how a deadline is worked out:

```
Letter dated Mon 1 Dec 2025
+ 4 days until it counts as delivered   Fri 5 Dec 2025
+ 1 month appeal period                 Mon 5 Jan 2026
Deadline: Mon 5 Jan 2026, end of the day
```

## Which AI reads the letter

You choose one in `backend/.env` (the file `backend/.env.example` shows all the options):

* Ollama, a model that runs on your own computer. It's free and the letter never leaves your machine. The default model is qwen2.5vl:7b.
* Groq, a hosted model with a free tier. You need a free API key from console.groq.com.
* Claude from Anthropic. This one is paid, but it's the most accurate.

## How it's built

The frontend is Next.js 16 with TypeScript and Tailwind CSS. The backend is Python with FastAPI and SQLModel, using SQLite on your machine and Postgres if you deploy it. Public holidays come from the holidays package, the PDF letters are made with fpdf2, and the GiroCode with segno.

## Running it on your computer

You need Python 3.12 or newer and Node.js 20 or newer.

First get a model. The easiest free option is Ollama:

```bash
brew install ollama
ollama serve
ollama pull qwen2.5vl:7b
```

The model is about 6 GB and needs around 8 GB of free memory. If that's too much for your laptop, use Groq or Claude instead (see above).

Then start the backend. It runs on http://localhost:8010:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8010
```

And the frontend in a second terminal. It runs on http://localhost:3000:

```bash
cd frontend
npm install
npm run dev
```

Even without any model you can use the deadline calculator and the glossary.

To run the tests:

```bash
cd backend && .venv/bin/python -m pytest
cd frontend && npm run lint && npm run build
```

## Where things are

```
backend/app/deadlines     the deadline rules
backend/app/extraction    reading letters with the different models
backend/app/knowledge     letter types and the glossary
backend/app/replies       German reply templates and the PDF letter
backend/app/services      calendar file, GiroCode, the result card
backend/tests             tests
frontend/app              the pages
frontend/components       the building blocks of the pages
docs                      architecture notes and legal notes
```

## Please note

Briefly gives you information, not legal or tax advice. It explains, translates, calculates deadlines and offers templates, but you decide what to send. Always compare the dates and amounts with your original letter. There's more about this in [docs/LEGAL.md](docs/LEGAL.md).

## What I'd like to add next

* A second check of amounts and IBANs with OCR
* Syncing with Google and Outlook calendars, and push reminders
* Filling in official forms, like the ones from the Beitragsservice or your local Ausländerbehörde
* A phone app with a document scanner
* More senders: health insurance, Familienkasse, Jobcenter, fines
