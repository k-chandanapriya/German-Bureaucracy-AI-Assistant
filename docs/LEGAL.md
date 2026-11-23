# Legal and compliance notes

These notes are a working checklist, not legal advice. Get a written opinion before launch.

| Topic | Risk | How the product handles it |
|---|---|---|
| **Rechtsdienstleistungsgesetz (RDG)** | Advice on a specific person's legal case is reserved for lawyers | The app explains, translates, computes deadlines and offers templates the user chooses. It never recommends whether to appeal. "Should I appeal?" goes to partner lawyers. |
| **Steuerberatungsgesetz (StBerG)** | Help with someone else's tax matters is reserved for Steuerberater / Lohnsteuerhilfevereine | Same approach; the advice tier is delivered by partners. |
| **GDPR** | Letters contain Steuer-ID, income, passport and residence data | EU hosting, data minimisation (photos not stored), deletion per case, DPA with the AI provider, DPIA before launch, no training on user letters without opt-in. |
| **EU AI Act** | Transparency for AI systems interacting with people | AI is labelled in the UI with a confidence indicator; the system assists and decides nothing. |
| **Liability** | A wrong deadline leads to a missed appeal | Deterministic, tested deadline engine; conservative (earlier) dates; "check with the original letter" prompts; clear terms; professional liability insurance. |

## Before production

- [ ] RDG / StBerG legal opinion
- [ ] Every reply template reviewed by a lawyer or Steuerberater
- [ ] DPIA (Datenschutz-Folgenabschätzung) and records of processing
- [ ] DPAs with hosting and AI providers (EU data processing)
- [ ] Terms of use and privacy policy (Impressum, Datenschutzerklärung)
