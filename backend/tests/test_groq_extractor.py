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


def _error(status: int, message: str, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json={"error": {"message": message}}, headers=headers,
                          request=httpx.Request("POST", "https://x"))


def test_wait_time_read_from_message(monkeypatch):
    responses = [_error(429, "Rate limit reached on tokens per minute (TPM): Limit 8000. Please try again in 1m7.5s."), _answer("ok")]
    stages = []
    monkeypatch.setattr(groq_extractor.httpx, "post", lambda *a, **k: responses.pop(0))
    assert groq_extractor._chat({"messages": []}, stages.append) == "ok"
    assert stages == ["Free AI service is busy, waiting 60s"]


def test_request_too_large_is_not_retried(monkeypatch):
    calls = []

    def post(*a, **k):
        calls.append(1)
        return _error(413, "Request too large for model on tokens per minute (TPM): Limit 8000, Requested 9500")

    monkeypatch.setattr(groq_extractor.httpx, "post", post)
    with pytest.raises(ExtractionError, match="too long for the free AI service"):
        groq_extractor._chat({"messages": []}, lambda _: None)
    assert len(calls) == 1


def test_daily_limit_is_not_retried(monkeypatch):
    monkeypatch.setattr(groq_extractor.httpx, "post", lambda *a, **k: _error(429, "Rate limit reached on tokens per day (TPD): Limit 200000"))
    with pytest.raises(ExtractionError, match="daily limit"):
        groq_extractor._chat({"messages": []}, lambda _: None)


def test_reasoning_switch_dropped_if_unsupported(monkeypatch):
    payloads = []

    def post(url, json, headers, timeout):
        payloads.append(dict(json))
        if "reasoning_effort" in json:
            return _error(400, "`reasoning_effort` is not supported with this model")
        return _answer("ok")

    monkeypatch.setattr(groq_extractor, "_reasoning_param_ok", True)
    monkeypatch.setattr(groq_extractor.httpx, "post", post)
    assert groq_extractor._chat({"messages": []}, lambda _: None) == "ok"
    assert payloads[0]["reasoning_effort"] == "none" and "reasoning_effort" not in payloads[1]
