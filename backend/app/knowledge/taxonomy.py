"""Letter-type taxonomy for v1: Finanzamt, Ausländerbehörde, Beitragsservice.

Each type says which law governs its deadlines, which appeal period applies
(if the letter is a Verwaltungsakt with a Rechtsbehelfsbelehrung), what
usually happens if the user ignores it, and which reply templates fit.
The LLM classifies a letter into one of these ids; it never invents options.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from app.deadlines.engine import LegalBasis


@dataclass(frozen=True)
class LetterType:
    id: str
    sender: str  # finanzamt | auslaenderbehoerde | beitragsservice | other
    name_de: str
    name_en: str
    what_it_is: str
    severity: str  # info | action | urgent
    legal_basis: LegalBasis
    appeal_months: int | None = None  # Einspruch / Widerspruch period
    appeal_name: str | None = None
    ignore_consequence: str = ""
    reply_templates: tuple[str, ...] = field(default_factory=tuple)
    checklist: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["legal_basis"] = self.legal_basis.value
        return d


SENDERS = {
    "finanzamt": "Finanzamt (tax office)",
    "auslaenderbehoerde": "Ausländerbehörde (immigration office)",
    "beitragsservice": "ARD ZDF Deutschlandradio Beitragsservice (broadcasting fee)",
    "other": "Other sender",
}

_TYPES: list[LetterType] = [
    # ---------------- Finanzamt ----------------
    LetterType(
        id="fa_steuernummer",
        sender="finanzamt",
        name_de="Mitteilung der Steuernummer",
        name_en="Your tax number",
        what_it_is="The tax office tells you your Steuernummer. Keep it: you need it for invoices and every future letter.",
        severity="info",
        legal_basis=LegalBasis.AO,
        ignore_consequence="Nothing happens, but you'll need the number later.",
    ),
    LetterType(
        id="fa_fragebogen",
        sender="finanzamt",
        name_de="Fragebogen zur steuerlichen Erfassung",
        name_en="Tax registration questionnaire",
        what_it_is="You started self-employment or a business. The tax office wants details before it gives you a tax number. It must be filed electronically via ELSTER.",
        severity="action",
        legal_basis=LegalBasis.AO,
        ignore_consequence="Reminders, then a late-filing surcharge or an estimated assessment (Schätzung). You can't issue proper invoices without a tax number.",
        reply_templates=("fa_fristverlaengerung",),
        checklist=(
            "ELSTER account (activation letter takes ~2 weeks)",
            "Expected revenue and profit for this and next year",
            "Bank account (IBAN) for refunds",
            "Decision on Kleinunternehmerregelung (§ 19 UStG)",
        ),
    ),
    LetterType(
        id="fa_einkommensteuerbescheid",
        sender="finanzamt",
        name_de="Einkommensteuerbescheid",
        name_en="Income tax assessment",
        what_it_is="Your final income tax assessment for the year: refund or additional payment.",
        severity="action",
        legal_basis=LegalBasis.AO,
        appeal_months=1,
        appeal_name="Einspruch (objection)",
        ignore_consequence="After the objection period the assessment becomes final (bestandskräftig). Any payment due must be made by the printed date or late fees (Säumniszuschläge, 1% per month) apply.",
        reply_templates=("fa_einspruch", "fa_stundung"),
    ),
    LetterType(
        id="fa_vorauszahlungsbescheid",
        sender="finanzamt",
        name_de="Bescheid über Vorauszahlungen",
        name_en="Tax prepayment notice",
        what_it_is="You must prepay income tax quarterly (10 Mar, 10 Jun, 10 Sep, 10 Dec), based on the tax office's estimate of your income.",
        severity="action",
        legal_basis=LegalBasis.AO,
        appeal_months=1,
        appeal_name="Einspruch (objection)",
        ignore_consequence="Unpaid instalments cost 1% per month in late fees and lead to enforcement.",
        reply_templates=("fa_herabsetzung", "fa_einspruch", "fa_stundung"),
    ),
    LetterType(
        id="fa_erinnerung",
        sender="finanzamt",
        name_de="Erinnerung / Mahnung",
        name_en="Reminder (tax return or payment)",
        what_it_is="You missed a tax return or payment deadline. The tax office reminds you and sets a new deadline.",
        severity="urgent",
        legal_basis=LegalBasis.AO,
        ignore_consequence="Late-filing surcharge (Verspätungszuschlag), an estimated assessment, coercive fines (Zwangsgeld) or enforcement.",
        reply_templates=("fa_fristverlaengerung", "fa_stundung"),
    ),
    LetterType(
        id="fa_anforderung_unterlagen",
        sender="finanzamt",
        name_de="Anforderung von Unterlagen / Rückfrage",
        name_en="Request for documents / query",
        what_it_is="The tax office has questions about your return and wants receipts or explanations by a date.",
        severity="action",
        legal_basis=LegalBasis.AO,
        ignore_consequence="The tax office decides without your evidence, usually not in your favour.",
        reply_templates=("fa_antwort_rueckfrage", "fa_fristverlaengerung"),
    ),
    LetterType(
        id="fa_verspaetungszuschlag",
        sender="finanzamt",
        name_de="Festsetzung eines Verspätungszuschlags",
        name_en="Late-filing surcharge",
        what_it_is="You filed late, so the tax office charges a surcharge (at least €25 per month late).",
        severity="action",
        legal_basis=LegalBasis.AO,
        appeal_months=1,
        appeal_name="Einspruch (objection)",
        ignore_consequence="The surcharge becomes final and must be paid.",
        reply_templates=("fa_einspruch", "fa_stundung"),
    ),
    # ---------------- Ausländerbehörde ----------------
    LetterType(
        id="abh_termin",
        sender="auslaenderbehoerde",
        name_de="Terminbestätigung / Einladung",
        name_en="Appointment invitation",
        what_it_is="You have an appointment at the immigration office. Bring every listed document.",
        severity="urgent",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="Missing it can delay your permit; new appointments can take months. If your permit expires meanwhile you need a Fiktionsbescheinigung.",
        reply_templates=("abh_terminanfrage",),
        checklist=(
            "Valid passport",
            "Biometric photo (35×45 mm, not older than 6 months)",
            "Current residence permit",
            "Employment contract and last 3 salary slips",
            "Rental contract + Wohnungsgeberbestätigung / Meldebescheinigung",
            "Proof of health insurance",
            "Filled application form",
        ),
    ),
    LetterType(
        id="abh_unterlagen",
        sender="auslaenderbehoerde",
        name_de="Anforderung von Unterlagen",
        name_en="Request for documents",
        what_it_is="The immigration office needs more documents before it can decide on your application.",
        severity="urgent",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="Your application can be refused for lack of cooperation (Mitwirkungspflicht).",
        reply_templates=("abh_unterlagen_anschreiben",),
    ),
    LetterType(
        id="abh_fiktionsbescheinigung",
        sender="auslaenderbehoerde",
        name_de="Fiktionsbescheinigung",
        name_en="Provisional residence certificate",
        what_it_is="Proof that your current status continues while your application is processed. Check the expiry date.",
        severity="info",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="Nothing, but you need to renew it before it expires if no decision has arrived.",
        reply_templates=("abh_fiktionsbescheinigung", "sachstandsanfrage"),
    ),
    LetterType(
        id="abh_abholung",
        sender="auslaenderbehoerde",
        name_de="Abholbenachrichtigung / Zustimmung",
        name_en="Approval / pick-up notice",
        what_it_is="Your permit (eAT card) is ready. Pick it up in person, usually with your passport and the PIN letter.",
        severity="action",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="The card stays at the office; your old document may expire.",
        checklist=("Passport", "Old permit / Fiktionsbescheinigung", "PIN letter from Bundesdruckerei", "Fee (often €100 or more)"),
    ),
    LetterType(
        id="abh_anhoerung",
        sender="auslaenderbehoerde",
        name_de="Anhörung",
        name_en="Hearing before a negative decision",
        what_it_is="The office plans a negative decision (refusal, shortened permit) and gives you a chance to respond first. This is serious.",
        severity="urgent",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="The office decides without your side of the story, most likely against you.",
        reply_templates=("fa_fristverlaengerung",),
    ),
    LetterType(
        id="abh_ablehnung",
        sender="auslaenderbehoerde",
        name_de="Ablehnungsbescheid",
        name_en="Rejection notice",
        what_it_is="Your application was refused. The Rechtsbehelfsbelehrung says whether you can object (Widerspruch) or must sue (Klage) and by when.",
        severity="urgent",
        legal_basis=LegalBasis.VWVFG,
        appeal_months=1,
        appeal_name="Widerspruch or Klage (see the letter)",
        ignore_consequence="The refusal becomes final; you may have to leave Germany. Talk to an immigration lawyer now.",
    ),
    # ---------------- Beitragsservice ----------------
    LetterType(
        id="rb_anmeldung",
        sender="beitragsservice",
        name_de="Begrüßungsschreiben / Anmeldung",
        name_en="Broadcasting fee welcome / registration",
        what_it_is="Every household pays the Rundfunkbeitrag (€18.36/month since 2025). You were registered based on your address registration.",
        severity="action",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="You get registered anyway and receive a payment request, later a Festsetzungsbescheid with an €8 late fee.",
        reply_templates=("rb_abmeldung", "rb_befreiung"),
    ),
    LetterType(
        id="rb_zahlungsaufforderung",
        sender="beitragsservice",
        name_de="Zahlungsaufforderung",
        name_en="Payment request",
        what_it_is="The Beitragsservice asks you to pay the broadcasting fee for the listed period.",
        severity="action",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="A Festsetzungsbescheid follows with a late fee (Säumniszuschlag, at least €8).",
        reply_templates=("rb_abmeldung", "rb_befreiung", "rb_ratenzahlung"),
    ),
    LetterType(
        id="rb_zahlungserinnerung",
        sender="beitragsservice",
        name_de="Zahlungserinnerung",
        name_en="Payment reminder",
        what_it_is="You haven't paid yet. This is a reminder before formal assessment.",
        severity="urgent",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="Festsetzungsbescheid with late fees, then enforcement.",
        reply_templates=("rb_abmeldung", "rb_ratenzahlung"),
    ),
    LetterType(
        id="rb_festsetzungsbescheid",
        sender="beitragsservice",
        name_de="Festsetzungsbescheid",
        name_en="Formal fee assessment",
        what_it_is="A formal decision setting the unpaid amount plus a late fee. You can object within one month.",
        severity="urgent",
        legal_basis=LegalBasis.VWVFG,
        appeal_months=1,
        appeal_name="Widerspruch (objection)",
        ignore_consequence="It becomes enforceable: the city's enforcement office (Vollstreckungsbehörde) can seize money from your bank account.",
        reply_templates=("rb_widerspruch", "rb_ratenzahlung"),
    ),
    LetterType(
        id="rb_vollstreckung",
        sender="beitragsservice",
        name_de="Ankündigung der Zwangsvollstreckung",
        name_en="Notice of enforcement",
        what_it_is="The debt has been handed to enforcement. Pay now or agree instalments immediately.",
        severity="urgent",
        legal_basis=LegalBasis.VWVFG,
        ignore_consequence="Bank account seizure (Kontopfändung), bailiff visit, extra costs.",
        reply_templates=("rb_ratenzahlung",),
    ),
    LetterType(
        id="rb_befreiung_bescheid",
        sender="beitragsservice",
        name_de="Befreiungs- / Ermäßigungsbescheid",
        name_en="Exemption decision",
        what_it_is="Decision on your exemption or reduction request (e.g. BAföG, Bürgergeld). Note the end date: you must re-apply before it runs out.",
        severity="info",
        legal_basis=LegalBasis.VWVFG,
        appeal_months=1,
        appeal_name="Widerspruch (objection)",
        ignore_consequence="If it's an approval: nothing, until it expires. If it's a refusal: you have to pay.",
        reply_templates=("rb_widerspruch", "rb_befreiung"),
    ),
    LetterType(
        id="other",
        sender="other",
        name_de="Sonstiges Schreiben",
        name_en="Other letter",
        what_it_is="This letter type is not covered in detail yet. We still extract dates and amounts.",
        severity="info",
        legal_basis=LegalBasis.VWVFG,
        reply_templates=("sachstandsanfrage",),
    ),
]

LETTER_TYPES: dict[str, LetterType] = {t.id: t for t in _TYPES}


def get_letter_type(type_id: str) -> LetterType:
    return LETTER_TYPES.get(type_id, LETTER_TYPES["other"])
