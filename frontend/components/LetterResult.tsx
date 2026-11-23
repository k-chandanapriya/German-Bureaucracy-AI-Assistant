"use client";

import Link from "next/link";
import { useState } from "react";
import CopyButton from "@/components/CopyButton";
import { CornerTicks } from "@/components/Frame";
import DeadlineList from "@/components/DeadlineList";
import ReplyDrafter from "@/components/ReplyDrafter";
import { api, deDate, euro, type LetterCard, type Meta } from "@/lib/api";

const SEVERITY = {
  info: { dot: "bg-emerald-500", text: "For your information", cls: "border-emerald-600/60 text-emerald-800" },
  action: { dot: "bg-accent", text: "Action may be needed", cls: "border-accent text-accent" },
  urgent: { dot: "bg-red-500", text: "Act now", cls: "border-red-500 text-red-700" },
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card space-y-4">
      <CornerTicks className="border-ink/30" />
      <h2 className="mono-label flex items-center gap-3">
        <span className="h-px w-5 bg-accent" />
        {title}
      </h2>
      {children}
    </section>
  );
}

export default function LetterResult({ initial, meta }: { initial: LetterCard; meta: Meta | null }) {
  const [card, setCard] = useState(initial);
  const [depth, setDepth] = useState<"tldr" | "details" | "lines">("tldr");
  const [templateId, setTemplateId] = useState<string | null>(null);
  const [fix, setFix] = useState({ letter_date: initial.letter_date ?? "", received_date: "" });
  const [fixing, setFixing] = useState(false);
  const [checked, setChecked] = useState<Record<number, boolean>>({});

  const sev = SEVERITY[card.severity];
  const template = meta?.reply_templates.find((t) => t.id === templateId);

  const recompute = async () => {
    setFixing(true);
    try {
      setCard(
        await api.recompute(card.letter_id, {
          letter_date: fix.letter_date || undefined,
          received_date: fix.received_date || undefined,
        }),
      );
    } finally {
      setFixing(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <section className="card space-y-4 p-6 sm:p-8">
        <CornerTicks />
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className={`flex items-center gap-2 border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.14em] ${sev.cls}`}>
            <span className={`h-1.5 w-1.5 ${sev.dot}`} />
            {sev.text}
          </span>
          <span className="mono-label">{card.sender.name}</span>
          <span className="text-ink/30">/</span>
          <span className="mono-label">Dated {deDate(card.letter_date)}</span>
        </div>
        <h1 className="text-3xl font-medium leading-tight sm:text-4xl">{card.title}</h1>
        <p className="text-sm text-ink/55">
          {card.letter_type.name_de} — {card.letter_type.name_en}
        </p>
        {card.linked_to_existing_case && (
          <p className="border border-line bg-paper px-3 py-2 text-sm text-ink/75">
            This letter has the same reference number as an earlier one, so we added it to that{" "}
            <Link href={`/cases/${card.case_id}`} className="underline">
              case
            </Link>
            .
          </p>
        )}

        <div className="flex gap-1 bg-ink/5 p-1 text-sm">
          {(
            [
              ["tldr", "In short"],
              ["details", "Details"],
              ["lines", "Line by line"],
            ] as const
          ).map(([k, label]) => (
            <button
              key={k}
              onClick={() => setDepth(k)}
              className={`flex-1 px-3 py-1.5 ${depth === k ? "bg-paper-2 font-medium shadow-sm" : "text-ink/65"}`}
            >
              {label}
            </button>
          ))}
        </div>
        {depth === "tldr" && <p className="text-lg leading-relaxed">{card.tldr}</p>}
        {depth === "details" && (
          <div className="space-y-2 text-ink/75">
            <p>{card.details}</p>
            <p className="text-sm text-ink/55">{card.what_it_is}</p>
          </div>
        )}
        {depth === "lines" && (
          <table className="w-full text-sm">
            <tbody>
              {card.line_by_line.map((l, i) => (
                <tr key={i} className="border-b border-line align-top">
                  <td className="w-1/2 py-2 pr-3 font-mono text-xs text-ink/65">{l.de}</td>
                  <td className="py-2">{l.en}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {card.warnings.length > 0 && (
        <section className="card space-y-3 border-accent/60 bg-accent/5">
          <h2 className="font-medium text-ink/80">⚠ Please confirm these with the original letter</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-ink/80">
            {card.warnings.map((w, i) => (
              <li key={i}>{w}</li>
            ))}
          </ul>
        </section>
      )}

      {card.check_this.length > 0 && (
        <Section title="Check this">
          <ul className="space-y-1">
            {card.check_this.map((c, i) => (
              <li key={i} className="flex gap-3"><span className="font-mono text-accent">!</span>{c}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Deadlines">
        <DeadlineList deadlines={card.deadlines} />
        <div className="flex flex-wrap items-end gap-3 border-t border-line pt-3">
          {card.deadlines.length > 0 && (
            <a className="btn-primary" href={api.icsUrl(card.letter_id)}>
              Add to calendar (.ics) ↗
            </a>
          )}
          <details className="text-sm">
            <summary className="cursor-pointer text-ink/65">Wrong date? Correct it</summary>
            <div className="mt-2 flex flex-wrap items-end gap-2">
              <label>
                <span className="label">Letter date</span>
                <input type="date" className="input" value={fix.letter_date} onChange={(e) => setFix({ ...fix, letter_date: e.target.value })} />
              </label>
              <label>
                <span className="label">Actually received (optional)</span>
                <input type="date" className="input" value={fix.received_date} onChange={(e) => setFix({ ...fix, received_date: e.target.value })} />
              </label>
              <button className="btn-secondary" onClick={recompute} disabled={fixing}>
                Recalculate
              </button>
            </div>
          </details>
        </div>
        <p className="text-xs text-ink/55">Reminders are set 7, 3 and 1 day before. Holidays: {meta?.bundeslaender[card.bundesland] ?? card.bundesland}.</p>
      </Section>

      {(card.amounts.length > 0 || card.payment) && (
        <Section title="Money">
          <ul className="space-y-1">
            {card.amounts.map((a, i) => (
              <li key={i} className="flex justify-between gap-4">
                <span>{a.label}</span>
                <span
                  className={`font-medium ${a.direction === "you_receive" ? "text-emerald-700" : a.direction === "you_pay" ? "text-red-700" : "text-ink/55"}`}
                >
                  {a.direction === "you_receive" ? "+" : a.direction === "you_pay" ? "−" : ""}
                  {euro(a.amount_eur)}
                </span>
              </li>
            ))}
          </ul>
          {card.payment && (
            <div className="grid gap-4 bg-paper p-4 sm:grid-cols-[1fr_auto]">
              <dl className="space-y-2 text-sm">
                {[
                  ["Recipient", card.payment.recipient],
                  ["IBAN", card.payment.iban],
                  ["BIC", card.payment.bic],
                  ["Reference (Verwendungszweck)", card.payment.reference],
                  ["Amount", card.payment.amount_eur ? euro(card.payment.amount_eur) : null],
                ]
                  .filter(([, v]) => v)
                  .map(([k, v]) => (
                    <div key={k}>
                      <dt className="label">{k}</dt>
                      <dd className="flex items-center gap-2 font-mono">
                        {v} <CopyButton text={String(v).replace(/\s/g, k === "IBAN" ? "" : " ")} />
                      </dd>
                    </div>
                  ))}
                {!card.payment.iban_valid && <p className="text-red-700">The IBAN looks wrong. Copy it from the letter.</p>}
              </dl>
              {card.payment.iban_valid && (
                <div className="text-center">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={api.girocodeUrl(card.letter_id)} alt="GiroCode for your banking app" className="h-40 w-40" />
                  <p className="text-xs text-ink/55">Scan with your banking app</p>
                </div>
              )}
            </div>
          )}
        </Section>
      )}

      <Section title="What you can do">
        {card.required_actions.length > 0 && (
          <ul className="list-disc space-y-1 pl-5">
            {card.required_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        )}
        {card.reply_templates.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {card.reply_templates.map((t) => (
              <button key={t.id} className="btn-secondary" onClick={() => setTemplateId(t.id)}>
                {t.title} ↗
              </button>
            ))}
          </div>
        )}
        {card.if_ignored && (
          <p className="bg-ink/5 px-3 py-2 text-sm">
            <span className="font-medium">If you do nothing: </span>
            {card.if_ignored}
          </p>
        )}
      </Section>

      {card.checklist.length > 0 && (
        <Section title="Documents checklist">
          <ul className="space-y-1">
            {card.checklist.map((c, i) => (
              <li key={i}>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={!!checked[i]} onChange={(e) => setChecked({ ...checked, [i]: e.target.checked })} />
                  <span className={checked[i] ? "text-ink/40 line-through" : ""}>{c}</span>
                </label>
              </li>
            ))}
          </ul>
        </Section>
      )}

      {card.reference_numbers.length > 0 && (
        <Section title="Reference numbers (quote these in every reply)">
          <dl className="grid gap-2 sm:grid-cols-2">
            {card.reference_numbers.map((r) => (
              <div key={r.label + r.value}>
                <dt className="label">{r.label}</dt>
                <dd className="flex items-center gap-2 font-mono">
                  {r.value} <CopyButton text={r.value} />
                </dd>
              </div>
            ))}
          </dl>
        </Section>
      )}

      {Object.keys(card.glossary).length > 0 && (
        <Section title="Words in this letter">
          <dl className="space-y-2 text-sm">
            {Object.entries(card.glossary).map(([term, def]) => (
              <div key={term}>
                <dt className="font-medium">{term}</dt>
                <dd className="text-ink/65">{def}</dd>
              </div>
            ))}
          </dl>
        </Section>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <Link href={`/cases/${card.case_id}`} className="btn-secondary">
          Open case →
        </Link>
        <span className="text-ink/55">AI confidence: {Math.round(card.confidence * 100)}%</span>
      </div>
      <p className="text-xs text-ink/55">{card.disclaimer}</p>

      {template && <ReplyDrafter template={template} card={card} onClose={() => setTemplateId(null)} />}
    </div>
  );
}
