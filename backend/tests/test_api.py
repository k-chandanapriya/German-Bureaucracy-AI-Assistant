import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


OWNER = "test-browser-0000000001"


def client(owner: str = OWNER) -> TestClient:
    return TestClient(app, headers={"X-Briefly-Owner": owner})


def test_health_and_meta():
    with client() as c:
        assert c.get("/api/health").json()["status"] == "ok"
        meta = c.get("/api/meta").json()
        assert "BE" in meta["bundeslaender"]
        assert len(meta["letter_types"]) >= 19
        assert {s["id"] for s in meta["samples"]} == {"steuerbescheid", "rundfunk", "abh_termin"}


def test_sample_steuerbescheid_flow():
    with client() as c:
        card = c.post("/api/letters/sample/steuerbescheid?bundesland=BE").json()
        assert card["severity"] == "action"
        appeal = card["deadlines"][0]
        # 12 Nov 2026 + 4 = Mon 16 Nov → + 1 month = Wed 16 Dec 2026
        assert appeal["due_date"] == "2026-12-16"
        assert "Einspruch" in appeal["label"]

        ics = c.get(f"/api/letters/{card['letter_id']}/calendar.ics")
        assert ics.status_code == 200
        assert "DTSTART;VALUE=DATE:20261216" in ics.text
        assert ics.text.count("BEGIN:VALARM") == 3

        # same Steuernummer → same case
        again = c.post("/api/letters/sample/steuerbescheid").json()
        assert again["case_id"] == card["case_id"]
        assert again["linked_to_existing_case"] is True


def test_rundfunk_payment_and_girocode():
    with client() as c:
        card = c.post("/api/letters/sample/rundfunk").json()
        assert card["payment"]["iban_valid"]
        assert card["payment"]["amount_eur"] == 63.08
        types = {d["type"] for d in card["deadlines"]}
        assert {"appeal", "payment"} <= types
        svg = c.get(f"/api/letters/{card['letter_id']}/girocode.svg")
        assert svg.status_code == 200 and "<svg" in svg.text


def test_recompute_with_received_date():
    with client() as c:
        card = c.post("/api/letters/sample/steuerbescheid").json()
        res = c.post(
            f"/api/letters/{card['letter_id']}/recompute",
            json={"received_date": "2026-11-20", "bundesland": "BY"},
        ).json()
        assert res["deadlines"][0]["due_date"] == "2026-12-21"  # 20 Dec is a Sunday


def test_deadline_calculator():
    with client() as c:
        r = c.post(
            "/api/deadlines/compute",
            json={"bundesland": "BE", "letter_date": "2025-12-01", "legal_basis": "AO", "period_length": 1, "period_unit": "months"},
        ).json()
        assert r["due_date"] == "2026-01-05"
        assert c.post("/api/deadlines/compute", json={"bundesland": "XX"}).status_code == 422


def test_reply_draft_prefill_and_pdf():
    with client() as c:
        card = c.post("/api/letters/sample/steuerbescheid").json()
        pre = c.get(f"/api/replies/prefill?template_id=fa_einspruch&letter_id={card['letter_id']}").json()
        assert pre["reference"] == "34/567/89012"
        assert pre["letter_date"] == "12.11.2026"

        missing = c.post("/api/replies/draft", json={"template_id": "fa_einspruch", "values": pre})
        assert missing.status_code == 422

        values = {**pre, "reason": "Die Kosten für mein Arbeitszimmer sind abzugsfähig.", "suspend": "no"}
        draft = c.post("/api/replies/draft", json={"template_id": "fa_einspruch", "values": values, "letter_id": card["letter_id"]}).json()
        assert "Einspruch" in draft["subject_de"]
        assert "34/567/89012" in draft["body_de"]
        assert "Aussetzung" not in draft["body_de"]

        pdf = c.post(
            "/api/replies/pdf",
            json={
                "subject_de": draft["subject_de"],
                "body_de": draft["body_de"],
                "sender_name": "Alex Example",
                "sender_address": "Musterstraße 1\n10115 Berlin",
                "recipient_address": "Finanzamt Berlin-Mitte\nNeue Jakobstraße 6-7\n10179 Berlin",
                "city": "Berlin",
            },
        )
        assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_cases_status_and_delete():
    with client() as c:
        card = c.post("/api/letters/sample/abh_termin").json()
        case = c.patch(f"/api/cases/{card['case_id']}", json={"status": "waiting"}).json()
        assert case["status"] == "waiting"
        assert case["timeline"][-1]["kind"] == "status_changed"
        assert c.patch(f"/api/cases/{card['case_id']}", json={"status": "bogus"}).status_code == 422
        assert any(x["id"] == card["case_id"] for x in c.get("/api/cases").json())
        assert c.delete(f"/api/cases/{card['case_id']}").status_code == 200
        assert c.get(f"/api/cases/{card['case_id']}").status_code == 404


def test_reading_job_reports_progress_and_result(monkeypatch):
    import time

    from app import main
    from app.extraction.errors import ExtractionError
    from app.extraction.samples import sample_extraction

    def fake_extract(payload, progress):
        progress("Reading page 1 of 2")
        return sample_extraction("abh_termin"), "fake"

    monkeypatch.setattr(main, "extract_letter", fake_extract)
    with client() as c:
        job = c.post("/api/letters/analyze/jobs", files={"files": ("a.png", b"x", "image/png")}, data={"bundesland": "BE"})
        assert job.status_code == 202
        jid = job.json()["id"]
        for _ in range(50):
            state = c.get(f"/api/jobs/{jid}").json()
            if state["status"] in ("done", "error"):
                break
            time.sleep(0.05)
        assert state["status"] == "done", state
        assert state["result"]["letter_type"]["id"] == "abh_termin"
        assert c.get(f"/api/letters/{state['result']['letter_id']}").status_code == 200

        def failing(payload, progress):
            raise ExtractionError("Can't reach Ollama")

        monkeypatch.setattr(main, "extract_letter", failing)
        jid = c.post("/api/letters/analyze/jobs", files={"files": ("a.png", b"x", "image/png")}).json()["id"]
        for _ in range(50):
            state = c.get(f"/api/jobs/{jid}").json()
            if state["status"] in ("done", "error"):
                break
            time.sleep(0.05)
        assert state == {**state, "status": "error", "error": "Can't reach Ollama"}
        assert c.get("/api/jobs/unknown").status_code == 404


def test_cases_are_private_to_their_browser():
    with client() as c:
        card = c.post("/api/letters/sample/abh_termin").json()
    with client("other-browser-000000002") as other:
        assert other.get(f"/api/letters/{card['letter_id']}").status_code == 404
        assert other.get(f"/api/cases/{card['case_id']}").status_code == 404
        assert other.delete(f"/api/cases/{card['case_id']}").status_code == 404
        assert all(x["id"] != card["case_id"] for x in other.get("/api/cases").json())
    with TestClient(app) as anonymous:
        assert anonymous.get("/api/cases").status_code == 401


def test_daily_read_limit(monkeypatch):
    from app import limits
    from app.config import settings

    monkeypatch.setattr(settings, "max_reads_per_ip_per_day", 1)
    monkeypatch.setattr(limits, "_per_ip", limits.Counter())
    monkeypatch.setattr("app.main.extract_letter", lambda files, progress=None: (_ for _ in ()).throw(RuntimeError("not called")))
    monkeypatch.setattr("app.main.jobs.submit", lambda *a, **k: type("J", (), {"to_dict": lambda self: {"id": "x"}})())
    with client() as c:
        upload = {"files": ("a.png", b"x", "image/png")}
        assert c.post("/api/letters/analyze/jobs", files=upload).status_code == 202
        assert c.post("/api/letters/analyze/jobs", files=upload).status_code == 429
