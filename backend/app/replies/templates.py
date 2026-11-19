"""Reply template library.

Templates are written once in German with an English back-translation and
filled with extracted data. The model never writes the legal text: it can
only fill fields. Before production every template must be reviewed by a
lawyer / Steuerberater (see docs/LEGAL.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from jinja2 import Environment, StrictUndefined, UndefinedError

_env = Environment(undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True, autoescape=False)


@dataclass(frozen=True)
class TemplateField:
    name: str
    label: str
    required: bool = True
    multiline: bool = False
    placeholder: str = ""


@dataclass(frozen=True)
class ReplyTemplate:
    id: str
    title_en: str
    subject_de: str
    body_de: str
    body_en: str
    channel_note: str
    fields: tuple[TemplateField, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title_en,
            "channel": self.channel_note,
            "fields": [f.__dict__ for f in self.fields],
        }


REF = TemplateField("reference", "Reference number (Steuernummer / Aktenzeichen / Beitragsnummer)")
LETTER_DATE = TemplateField("letter_date", "Date of their letter (DD.MM.YYYY)")
REASON = TemplateField("reason", "Your reason (in German, or simple English we'll keep as-is)", multiline=True)

WRITTEN = "Must be in writing: signed letter by post or fax, or via ELSTER. Email and phone don't count."
WRITTEN_BS = "Send by post or use the Beitragsservice online form (rundfunkbeitrag.de). Keep a copy."
WRITTEN_ABH = "Send by email or post to your case worker, quoting the Aktenzeichen. Keep a copy."

_TEMPLATES = [
    ReplyTemplate(
        id="fa_einspruch",
        title_en="Objection to a tax decision (Einspruch)",
        subject_de="Einspruch gegen den Bescheid vom {{ letter_date }}",
        body_de="""hiermit lege ich gegen den {{ decision_name }} vom {{ letter_date }} (Steuernummer {{ reference }}) fristgerecht Einspruch ein.

Begründung:
{{ reason }}

{% if suspend %}Gleichzeitig beantrage ich die Aussetzung der Vollziehung des streitigen Betrags gemäß § 361 AO.

{% endif %}Ich bitte um Bestätigung des Eingangs.""",
        body_en="""I hereby file a timely objection against the {{ decision_name }} dated {{ letter_date }} (tax number {{ reference }}).

Reason:
{{ reason }}

{% if suspend %}At the same time I request suspension of enforcement of the disputed amount under § 361 AO.

{% endif %}Please confirm receipt.""",
        channel_note=WRITTEN,
        fields=(
            REF,
            LETTER_DATE,
            TemplateField("decision_name", "Name of the decision", placeholder="Einkommensteuerbescheid 2025"),
            REASON,
            TemplateField("suspend", "Also request suspension of payment (yes/no)", required=False),
        ),
    ),
    ReplyTemplate(
        id="fa_fristverlaengerung",
        title_en="Request a deadline extension",
        subject_de="Antrag auf Fristverlängerung – {{ reference }}",
        body_de="""in der oben genannten Angelegenheit haben Sie mir mit Schreiben vom {{ letter_date }} eine Frist bis zum {{ current_deadline }} gesetzt.

Leider kann ich die Frist nicht einhalten, weil {{ reason }}

Ich beantrage daher, die Frist bis zum {{ new_deadline }} zu verlängern.""",
        body_en="""Regarding the matter above, your letter of {{ letter_date }} set a deadline of {{ current_deadline }}.

Unfortunately I cannot meet it because {{ reason }}

I therefore request an extension until {{ new_deadline }}.""",
        channel_note="Send before the current deadline ends. Post, fax or ELSTER message for the tax office.",
        fields=(
            REF,
            LETTER_DATE,
            TemplateField("current_deadline", "Current deadline (DD.MM.YYYY)"),
            TemplateField("new_deadline", "Requested new deadline (DD.MM.YYYY)"),
            REASON,
        ),
    ),
    ReplyTemplate(
        id="fa_stundung",
        title_en="Request deferral or instalments (Stundung / Ratenzahlung)",
        subject_de="Antrag auf Stundung / Ratenzahlung – {{ reference }}",
        body_de="""mit Bescheid vom {{ letter_date }} wurde ein Betrag von {{ amount }} € festgesetzt.

Die sofortige Zahlung in voller Höhe ist mir derzeit nicht möglich, weil {{ reason }}

Ich beantrage daher gemäß § 222 AO, den Betrag in monatlichen Raten von {{ monthly_rate }} € zu begleichen, beginnend am {{ start_date }}. Eine Aufstellung meiner Einnahmen und Ausgaben füge ich bei.""",
        body_en="""By decision dated {{ letter_date }} an amount of €{{ amount }} was set.

I can't pay the full amount immediately because {{ reason }}

Under § 222 AO I therefore request to pay in monthly instalments of €{{ monthly_rate }}, starting on {{ start_date }}. I enclose an overview of my income and expenses.""",
        channel_note="In writing or via ELSTER, before the due date. Interest of 0.5% per month may apply.",
        fields=(
            REF,
            LETTER_DATE,
            TemplateField("amount", "Amount (e.g. 1.250,00)"),
            TemplateField("monthly_rate", "Monthly instalment you can afford"),
            TemplateField("start_date", "First payment date (DD.MM.YYYY)"),
            REASON,
        ),
    ),
    ReplyTemplate(
        id="fa_herabsetzung",
        title_en="Request lower tax prepayments",
        subject_de="Antrag auf Herabsetzung der Vorauszahlungen – {{ reference }}",
        body_de="""mit Bescheid vom {{ letter_date }} wurden Vorauszahlungen zur Einkommensteuer festgesetzt.

Meine Einkünfte für {{ year }} werden voraussichtlich deutlich niedriger ausfallen, weil {{ reason }} Ich erwarte einen Gewinn von etwa {{ expected_profit }} €.

Ich beantrage daher, die Vorauszahlungen entsprechend herabzusetzen. Eine Prognoserechnung füge ich bei.""",
        body_en="""By decision dated {{ letter_date }} income tax prepayments were set.

My income for {{ year }} will likely be much lower because {{ reason }} I expect a profit of about €{{ expected_profit }}.

I therefore request that the prepayments be reduced accordingly. I enclose a forecast.""",
        channel_note="Letter or ELSTER message. No strict deadline, but the sooner the better.",
        fields=(
            REF,
            LETTER_DATE,
            TemplateField("year", "Year"),
            TemplateField("expected_profit", "Expected profit in € (e.g. 18.000)"),
            REASON,
        ),
    ),
    ReplyTemplate(
        id="fa_antwort_rueckfrage",
        title_en="Answer a tax office query",
        subject_de="Ihre Anfrage vom {{ letter_date }} – {{ reference }}",
        body_de="""vielen Dank für Ihr Schreiben vom {{ letter_date }}. Zu Ihren Fragen nehme ich wie folgt Stellung:

{{ answer }}

Die angeforderten Unterlagen füge ich bei:
{{ enclosures }}""",
        body_en="""Thank you for your letter of {{ letter_date }}. Here are my answers:

{{ answer }}

I enclose the requested documents:
{{ enclosures }}""",
        channel_note="Post or ELSTER message with attachments, before the deadline in their letter.",
        fields=(
            REF,
            LETTER_DATE,
            TemplateField("answer", "Your answers", multiline=True),
            TemplateField("enclosures", "List of enclosed documents", multiline=True),
        ),
    ),
    ReplyTemplate(
        id="rb_abmeldung",
        title_en="Deregister from the broadcasting fee",
        subject_de="Abmeldung – Beitragsnummer {{ reference }}",
        body_de="""hiermit melde ich meine Wohnung zum {{ end_date }} ab.

Grund: {{ reason }}
{% if other_number %}
Für die Wohnung wird bereits ein Rundfunkbeitrag unter der Beitragsnummer {{ other_number }} gezahlt.
{% endif %}

Bitte bestätigen Sie mir die Abmeldung schriftlich.""",
        body_en="""I hereby deregister my flat as of {{ end_date }}.

Reason: {{ reason }}
{% if other_number %}
The fee for this flat is already paid under contribution number {{ other_number }}.
{% endif %}

Please confirm the deregistration in writing.""",
        channel_note=WRITTEN_BS,
        fields=(
            REF,
            TemplateField("end_date", "Deregister as of (DD.MM.YYYY)"),
            TemplateField("reason", "Reason", placeholder="Umzug ins Ausland / Zusammenzug mit einer beitragszahlenden Person"),
            TemplateField("other_number", "Beitragsnummer of the person who already pays", required=False),
        ),
    ),
    ReplyTemplate(
        id="rb_befreiung",
        title_en="Apply for exemption (BAföG, Bürgergeld …)",
        subject_de="Antrag auf Befreiung von der Rundfunkbeitragspflicht – Beitragsnummer {{ reference }}",
        body_de="""hiermit beantrage ich die Befreiung von der Rundfunkbeitragspflicht gemäß § 4 Abs. 1 RBStV.

Ich beziehe {{ benefit }}. Den Bescheid (Kopie bzw. Bestätigung der Behörde) füge ich bei. Der Bewilligungszeitraum läuft vom {{ from_date }} bis zum {{ to_date }}.""",
        body_en="""I hereby apply for exemption from the broadcasting fee under § 4 (1) RBStV.

I receive {{ benefit }}. I enclose the decision (copy or the authority's confirmation). The approval period runs from {{ from_date }} to {{ to_date }}.""",
        channel_note=WRITTEN_BS + " Exemption applies at most 3 years back.",
        fields=(
            REF,
            TemplateField("benefit", "Benefit you receive", placeholder="BAföG / Bürgergeld"),
            TemplateField("from_date", "Approval period from"),
            TemplateField("to_date", "Approval period to"),
        ),
    ),
    ReplyTemplate(
        id="rb_widerspruch",
        title_en="Object to a broadcasting fee decision (Widerspruch)",
        subject_de="Widerspruch gegen den Bescheid vom {{ letter_date }} – Beitragsnummer {{ reference }}",
        body_de="""gegen Ihren Bescheid vom {{ letter_date }} lege ich hiermit Widerspruch ein.

Begründung:
{{ reason }}

Ich bitte um Eingangsbestätigung.""",
        body_en="""I hereby object to your decision of {{ letter_date }}.

Reason:
{{ reason }}

Please confirm receipt.""",
        channel_note="In writing and signed, by post, within one month. Email is not enough.",
        fields=(REF, LETTER_DATE, REASON),
    ),
    ReplyTemplate(
        id="rb_ratenzahlung",
        title_en="Request instalments for the broadcasting fee",
        subject_de="Bitte um Ratenzahlung – Beitragsnummer {{ reference }}",
        body_de="""den offenen Betrag von {{ amount }} € kann ich derzeit nicht auf einmal zahlen.

Ich bitte daher um Ratenzahlung in Höhe von {{ monthly_rate }} € monatlich, beginnend am {{ start_date }}. Die laufenden Beiträge zahle ich zusätzlich.""",
        body_en="""I can't currently pay the outstanding €{{ amount }} at once.

I therefore ask to pay €{{ monthly_rate }} per month, starting on {{ start_date }}. I'll pay the ongoing fees in addition.""",
        channel_note=WRITTEN_BS,
        fields=(
            REF,
            TemplateField("amount", "Outstanding amount"),
            TemplateField("monthly_rate", "Monthly instalment"),
            TemplateField("start_date", "Start date"),
        ),
    ),
    ReplyTemplate(
        id="abh_terminanfrage",
        title_en="Ask for a (new) appointment",
        subject_de="Bitte um Termin – Aktenzeichen {{ reference }}",
        body_de="""{% if old_date %}leider kann ich den Termin am {{ old_date }} nicht wahrnehmen, weil {{ reason }}

{% endif %}ich bitte um einen {% if old_date %}neuen {% endif %}Termin zur {{ purpose }}. Mein aktueller Aufenthaltstitel ist gültig bis zum {{ permit_expiry }}.

Sollte vor Ablauf kein Termin möglich sein, bitte ich um Ausstellung einer Fiktionsbescheinigung gemäß § 81 Abs. 4 AufenthG.""",
        body_en="""{% if old_date %}Unfortunately I can't attend the appointment on {{ old_date }} because {{ reason }}

{% endif %}I'm asking for {% if old_date %}a new{% else %}an{% endif %} appointment for {{ purpose }}. My current residence permit is valid until {{ permit_expiry }}.

If no appointment is possible before it expires, I request a Fiktionsbescheinigung under § 81 (4) AufenthG.""",
        channel_note=WRITTEN_ABH,
        fields=(
            REF,
            TemplateField("purpose", "Purpose", placeholder="Verlängerung meines Aufenthaltstitels"),
            TemplateField("permit_expiry", "Your permit expires on (DD.MM.YYYY)"),
            TemplateField("old_date", "Date of the appointment you must cancel", required=False),
            TemplateField("reason", "Why you can't attend", required=False),
        ),
    ),
    ReplyTemplate(
        id="abh_fiktionsbescheinigung",
        title_en="Request a Fiktionsbescheinigung",
        subject_de="Antrag auf Fiktionsbescheinigung – Aktenzeichen {{ reference }}",
        body_de="""am {{ application_date }} habe ich die Verlängerung meines Aufenthaltstitels beantragt. Mein Titel {% if expired %}ist am {{ permit_expiry }} abgelaufen{% else %}läuft am {{ permit_expiry }} ab{% endif %}, eine Entscheidung liegt noch nicht vor.

Ich bitte daher um Ausstellung einer Fiktionsbescheinigung gemäß § 81 Abs. 4 AufenthG, damit ich meine Beschäftigung ohne Unterbrechung fortsetzen und reisen kann.""",
        body_en="""On {{ application_date }} I applied to extend my residence permit. My permit {% if expired %}expired{% else %}expires{% endif %} on {{ permit_expiry }} and there is no decision yet.

I therefore request a Fiktionsbescheinigung under § 81 (4) AufenthG so I can keep working and travel without interruption.""",
        channel_note=WRITTEN_ABH,
        fields=(
            REF,
            TemplateField("application_date", "Date you applied (DD.MM.YYYY)"),
            TemplateField("permit_expiry", "Permit expiry date (DD.MM.YYYY)"),
            TemplateField("expired", "Already expired? (yes/no)", required=False),
        ),
    ),
    ReplyTemplate(
        id="abh_unterlagen_anschreiben",
        title_en="Cover letter for submitted documents",
        subject_de="Nachreichung von Unterlagen – Aktenzeichen {{ reference }}",
        body_de="""wie mit Ihrem Schreiben vom {{ letter_date }} angefordert, reiche ich folgende Unterlagen nach:

{{ enclosures }}

Bei Rückfragen erreichen Sie mich unter {{ contact }}.""",
        body_en="""As requested in your letter of {{ letter_date }}, I submit the following documents:

{{ enclosures }}

If you have questions, you can reach me at {{ contact }}.""",
        channel_note=WRITTEN_ABH,
        fields=(
            REF,
            LETTER_DATE,
            TemplateField("enclosures", "Documents (one per line)", multiline=True),
            TemplateField("contact", "Phone or email"),
        ),
    ),
    ReplyTemplate(
        id="sachstandsanfrage",
        title_en="Ask about the status of your case (Sachstandsanfrage)",
        subject_de="Sachstandsanfrage – {{ reference }}",
        body_de="""am {{ sent_date }} habe ich {{ what }} eingereicht. Bisher habe ich keine Antwort erhalten.

Ich bitte Sie um eine kurze Mitteilung zum aktuellen Bearbeitungsstand und, falls möglich, um eine Einschätzung, wann mit einer Entscheidung zu rechnen ist.""",
        body_en="""On {{ sent_date }} I submitted {{ what }}. I haven't received an answer yet.

Please let me know the current status and, if possible, when I can expect a decision.""",
        channel_note="Email or letter quoting the reference number. Typically after 6 weeks without an answer.",
        fields=(
            REF,
            TemplateField("sent_date", "Date you sent your application/letter"),
            TemplateField("what", "What you submitted", placeholder="meinen Antrag auf Verlängerung"),
        ),
    ),
]

REPLY_TEMPLATES: dict[str, ReplyTemplate] = {t.id: t for t in _TEMPLATES}

_YES = {"yes", "ja", "true", "1", "y"}


class TemplateFieldError(ValueError):
    pass


def render_reply(template_id: str, values: dict[str, str]) -> dict:
    tpl = REPLY_TEMPLATES.get(template_id)
    if not tpl:
        raise KeyError(template_id)

    ctx: dict[str, object] = {}
    missing = []
    for f in tpl.fields:
        v = (values.get(f.name) or "").strip()
        if not v and f.required:
            missing.append(f.label)
        ctx[f.name] = v
    for flag in ("suspend", "expired"):
        if flag in ctx:
            ctx[flag] = str(ctx[flag]).lower() in _YES
    if missing:
        raise TemplateFieldError("Please fill in: " + ", ".join(missing))

    try:
        return {
            "template_id": tpl.id,
            "subject_de": _env.from_string(tpl.subject_de).render(ctx),
            "body_de": _env.from_string(tpl.body_de).render(ctx).strip(),
            "body_en": _env.from_string(tpl.body_en).render(ctx).strip(),
            "channel": tpl.channel_note,
        }
    except UndefinedError as e:  # pragma: no cover - guarded by field list
        raise TemplateFieldError(str(e)) from e
