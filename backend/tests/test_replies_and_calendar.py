from datetime import date

import pytest

from app.replies.templates import REPLY_TEMPLATES, TemplateFieldError, render_reply
from app.services.calendar_ics import build_ics
from app.services.girocode import epc_payload


def test_every_template_renders_with_dummy_values():
    for tid, tpl in REPLY_TEMPLATES.items():
        values = {f.name: "01.01.2027" for f in tpl.fields}
        out = render_reply(tid, values)
        assert out["subject_de"] and out["body_de"] and out["body_en"], tid
        assert "{{" not in out["body_de"]


def test_missing_required_field():
    with pytest.raises(TemplateFieldError):
        render_reply("rb_widerspruch", {"reference": "123"})


def test_optional_block():
    vals = {"reference": "1", "end_date": "01.01.2027", "reason": "Umzug"}
    assert "bereits" not in render_reply("rb_abmeldung", vals)["body_de"]
    vals["other_number"] = "987654321"
    assert "987654321" in render_reply("rb_abmeldung", vals)["body_de"]


def test_ics_escaping_and_folding():
    ics = build_ics([{"title": "Pay; now, please", "date": date(2026, 12, 1), "description": "x" * 200}])
    assert "SUMMARY:Pay\\; now\\, please" in ics
    assert all(len(line.encode()) <= 75 for line in ics.split("\r\n"))


def test_epc_payload():
    p = epc_payload("Beitragsservice", "DE02 1203 0000 0000 2020 51", 63.08, "123456789")
    lines = p.split("\n")
    assert lines[:4] == ["BCD", "002", "1", "SCT"]
    assert lines[6] == "DE02120300000000202051"
    assert lines[7] == "EUR63.08"
    assert lines[-1] == "123456789"
