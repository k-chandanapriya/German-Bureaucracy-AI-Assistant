import io
import json

import httpx
import pytest
from PIL import Image

from app.config import settings
from app.extraction import groq_extractor
from app.extraction.errors import ExtractionError
from app.extraction.samples import SAMPLES


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (800, 1100), "white").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def key(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "test-key")
    monkeypatch.setattr(groq_extractor.time, "sleep", lambda s: None)


def _answer(content: str, status: int = 200, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json={"choices": [{"message": {"content": content}}]}, headers=headers,
                          request=httpx.Request("POST", "https://x"))


def test_transcribes_then_extracts(monkeypatch):
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append(json)
        if "response_format" not in json:
            return _answer("Beitragsservice\nDatum: 02.11.2026\nBeitragsnummer 123 456 789")
        answer = dict(SAMPLES["rundfunk"]["extraction"], confidence=0.99, letter_date=None)
        return _answer("<think>hmm</think>" + json_dumps(answer))

    json_dumps = json.dumps
    monkeypatch.setattr(groq_extractor.httpx, "post", fake_post)
    result, model = groq_extractor.extract_letter_groq([(_png(), "image/png")] * 2)

    assert model == f"groq:{settings.groq_model}"
    assert result.letter_type == "rb_festsetzungsbescheid"
    assert result.letter_date == "2026-11-02"  # filled in from the transcript
    assert result.confidence == 0.9
    assert len(calls) == 3
    image_part = calls[0]["messages"][0]["content"][1]
    assert image_part["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert calls[2]["response_format"] == {"type": "json_object"}
    assert "LetterExtraction" in calls[2]["messages"][0]["content"]


def test_waits_out_rate_limit(monkeypatch):
    responses = [
        httpx.Response(429, headers={"retry-after": "3"}, request=httpx.Request("POST", "https://x")),
        _answer("ok"),
    ]
    stages = []
    monkeypatch.setattr(groq_extractor.httpx, "post", lambda *a, **k: responses.pop(0))
    assert groq_extractor._chat({"messages": []}, stages.append) == "ok"
    assert stages == ["Free AI service is busy, waiting 3s"]


def test_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "")
    with pytest.raises(ExtractionError, match="GROQ_API_KEY"):
        groq_extractor._chat({"messages": []}, lambda _: None)


def test_bad_key(monkeypatch):
    monkeypatch.setattr(groq_extractor.httpx, "post", lambda *a, **k: httpx.Response(401, request=httpx.Request("POST", "https://x")))
    with pytest.raises(ExtractionError, match="rejected the API key"):
        groq_extractor._chat({"messages": []}, lambda _: None)
