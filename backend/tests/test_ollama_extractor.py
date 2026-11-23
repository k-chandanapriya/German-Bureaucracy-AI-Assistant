import io
import json

import httpx
import pytest
from PIL import Image

from app.extraction import ollama_extractor
from app.extraction.errors import ExtractionError
from app.extraction.images import MAX_SIDE, to_page_images
from app.extraction.samples import SAMPLES
from app.replies.letter_pdf import render_letter_pdf


def _png(w: int, h: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), "white").save(buf, format="PNG")
    return buf.getvalue()


def _pdf() -> bytes:
    return render_letter_pdf(
        sender_name="A",
        sender_address="Str. 1\n10115 Berlin",
        recipient_address="Finanzamt\n10179 Berlin",
        city="Berlin",
        subject="Test",
        body="Text",
    )


def test_large_photo_is_scaled_down_to_jpeg():
    [page] = to_page_images([(_png(4000, 3000), "image/png")])
    img = Image.open(io.BytesIO(page))
    assert img.format == "JPEG"
    assert max(img.size) == MAX_SIDE


def test_pdf_is_rendered_to_page_images():
    pages = to_page_images([(_pdf(), "application/pdf"), (_png(800, 1100), "image/jpeg")])
    assert len(pages) == 2
    assert all(p[:2] == b"\xff\xd8" for p in pages)  # JPEG magic bytes


def test_rejects_unsupported_and_broken_files():
    with pytest.raises(ExtractionError):
        to_page_images([(b"hello", "text/plain")])
    with pytest.raises(ExtractionError):
        to_page_images([(b"not an image", "image/png")])


def test_ollama_request_and_parsing(monkeypatch):
    calls = []

    def fake_post(payload):
        calls.append(payload)
        if "format" not in payload:  # pass 1: transcription
            return {"message": {"content": "Beitragsservice\nDatum: 02.11.2026\nBeitragsnummer 123 456 789"}}
        answer = dict(SAMPLES["rundfunk"]["extraction"], confidence=0.99, letter_date=None)
        return {"message": {"role": "assistant", "content": json.dumps(answer)}}

    monkeypatch.setattr(ollama_extractor, "_post", fake_post)
    result, model = ollama_extractor.extract_letter_ollama([(_png(800, 1100), "image/png")] * 2)

    assert model.startswith("ollama:")
    assert result.letter_type == "rb_festsetzungsbescheid"
    assert result.letter_date == "2026-11-02"  # filled from the transcript
    assert result.confidence == 0.9  # capped for local models
    assert len(calls) == 3  # two pages transcribed, one extraction
    assert all(len(c["messages"][0]["images"]) == 1 for c in calls[:2])
    assert calls[2]["format"]["title"] == "LetterExtraction"
    assert "--- Page 2 ---" in calls[2]["messages"][1]["content"]


def test_ollama_invalid_json(monkeypatch):
    def fake_post(p):
        if "format" not in p:
            return {"message": {"content": "Some readable letter text, long enough to pass the check."}}
        return {"message": {"content": '{"oops": 1}'}}

    monkeypatch.setattr(ollama_extractor, "_post", fake_post)
    with pytest.raises(ExtractionError, match="didn't match"):
        ollama_extractor.extract_letter_ollama([(_png(10, 10), "image/png")])


def test_ollama_not_running(monkeypatch):
    def refuse(*a, **k):
        raise httpx.ConnectError("refused")

    monkeypatch.setattr(httpx, "post", refuse)
    with pytest.raises(ExtractionError, match="Can't reach Ollama"):
        ollama_extractor.extract_letter_ollama([(_png(10, 10), "image/png")])


def test_model_not_pulled(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(404, json={"error": "model not found"}))
    with pytest.raises(ExtractionError, match="ollama pull"):
        ollama_extractor.extract_letter_ollama([(_png(10, 10), "image/png")])


def test_blank_page(monkeypatch):
    monkeypatch.setattr(ollama_extractor, "_post", lambda p: {"message": {"content": ""}})
    with pytest.raises(ExtractionError, match="No readable text"):
        ollama_extractor.extract_letter_ollama([(_png(10, 10), "image/png")])


def test_digital_pdf_uses_text_layer_without_vision(monkeypatch):
    from app.extraction.images import to_pages

    long_body = "Bescheid über Vorauszahlungen. " * 10
    pdf = render_letter_pdf(
        sender_name="A", sender_address="Str. 1\n10115 Berlin", recipient_address="Finanzamt\n10179 Berlin",
        city="Berlin", subject="Test", body=long_body,
    )
    [page] = to_pages([(pdf, "application/pdf")])
    assert page.image is None and "Vorauszahlungen" in page.text

    calls = []

    def fake_post(payload):
        calls.append(payload)
        return {"message": {"content": json.dumps(SAMPLES["steuerbescheid"]["extraction"])}}

    monkeypatch.setattr(ollama_extractor, "_post", fake_post)
    stages = []
    ollama_extractor.extract_letter_ollama([(pdf, "application/pdf")], stages.append)
    assert len(calls) == 1 and "format" in calls[0]  # no vision call, straight to extraction
    assert "Understanding the letter" in stages
