"use client";

import Link from "next/link";
import { useState } from "react";
import CopyButton from "@/components/CopyButton";
import DeadlineList from "@/components/DeadlineList";
import ReplyDrafter from "@/components/ReplyDrafter";
import { api, deDate, euro, type LetterCard, type Meta } from "@/lib/api";

const SEVERITY = {
  info: { icon: "🟢", text: "For your information", cls: "bg-emerald-50 text-emerald-800 border-emerald-200" },
  action: { icon: "🟡", text: "Action may be needed", cls: "bg-amber-50 text-amber-800 border-amber-200" },
  urgent: { icon: "🔴", text: "Act now", cls: "bg-red-50 text-red-800 border-red-200" },
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="card space-y-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">{title}</h2>
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
      <section className="card space-y-3">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className={`rounded-full border px-2.5 py-0.5 font-medium ${sev.cls}`}>
            {sev.icon} {sev.text}
          </span>
          <span className="text-stone-500">{card.sender.name}</span>
          <span className="text-stone-400">·</span>
          <span className="text-stone-500">dated {deDate(card.letter_date)}</span>
        </div>
        <h1 className="text-2xl font-bold">{card.title}</h1>
        <p className="text-sm text-stone-500">
          {card.letter_type.name_de} — {card.letter_type.name_en}
        </p>
        {card.linked_to_existing_case && (
          <p className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-800">
            🔗 This letter has the same reference number as an earlier one, so we added it to that{" "}
            <Link href={`/cases/${card.case_id}`} className="underline">
              case
            </Link>
            .
          </p>
        )}

        <div className="flex gap-1 rounded-lg bg-stone-100 p-1 text-sm">
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
              className={`flex-1 rounded-md px-3 py-1.5 ${depth === k ? "bg-white font-medium shadow-sm" : "text-stone-600"}`}
            >
              {label}
            </button>
          ))}
        </div>
        {depth === "tldr" && <p className="text-lg leading-relaxed">{card.tldr}</p>}
        {depth === "details" && (
          <div className="space-y-2 text-stone-700">
            <p>{card.details}</p>
            <p className="text-sm text-stone-500">{card.what_it_is}</p>
          </div>
        )}
        {depth === "lines" && (
          <table className="w-full text-sm">
            <tbody>
              {card.line_by_line.map((l, i) => (
                <tr key={i} className="border-b border-stone-100 align-top">
                  <td className="w-1/2 py-2 pr-3 font-mono text-xs text-stone-600">{l.de}</td>
                  <td className="py-2">{l.en}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {card.warnings.length > 0 && (
        <section className="card space-y-3 border-amber-300 bg-amber-50">
          <h2 className="font-semibold text-amber-900">⚠ Please confirm these with the original letter</h2>
          <ul className="list-disc space-y-1 pl-5 text-sm text-amber-900">
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
              <li key={i}>⚠️ {c}</li>
            ))}
          </ul>
        </Section>
      )}

      <Section title="Deadlines">
        <DeadlineList deadlines={card.deadlines} />
        <div className="flex flex-wrap items-end gap-3 border-t border-stone-100 pt-3">
          {card.deadlines.length > 0 && (
            <a className="btn-primary" href={api.icsUrl(card.letter_id)}>
              📅 Add to calendar (.ics)
            </a>
          )}
          <details className="text-sm">
            <summary className="cursor-pointer text-stone-600">Wrong date? Correct it</summary>
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
        <p className="text-xs text-stone-500">Reminders are set 7, 3 and 1 day before. Holidays: {meta?.bundeslaender[card.bundesland] ?? card.bundesland}.</p>
      </Section>

      {(card.amounts.length > 0 || card.payment) && (
        <Section title="Money">
          <ul className="space-y-1">
            {card.amounts.map((a, i) => (
              <li key={i} className="flex justify-between gap-4">
                <span>{a.label}</span>
                <span
                  className={`font-semibold ${a.direction === "you_receive" ? "text-emerald-700" : a.direction === "you_pay" ? "text-red-700" : "text-stone-500"}`}
                >
                  {a.direction === "you_receive" ? "+" : a.direction === "you_pay" ? "−" : ""}
                  {euro(a.amount_eur)}
                </span>
              </li>
            ))}
          </ul>
          {card.payment && (
            <div className="grid gap-4 rounded-xl bg-stone-50 p-4 sm:grid-cols-[1fr_auto]">
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
                  <p className="text-xs text-stone-500">Scan with your banking app</p>
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
                ✍️ {t.title}
              </button>
            ))}
          </div>
        )}
        {card.if_ignored && (
          <p className="rounded-lg bg-stone-100 px-3 py-2 text-sm">
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
                  <span className={checked[i] ? "text-stone-400 line-through" : ""}>{c}</span>
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
                <dt className="font-semibold">{term}</dt>
                <dd className="text-stone-600">{def}</dd>
              </div>
            ))}
          </dl>
        </Section>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
        <Link href={`/cases/${card.case_id}`} className="btn-secondary">
          Open case →
        </Link>
        <span className="text-stone-500">AI confidence: {Math.round(card.confidence * 100)}%</span>
      </div>
      <p className="text-xs text-stone-500">{card.disclaimer}</p>

      {template && <ReplyDrafter template={template} card={card} onClose={() => setTemplateId(null)} />}
    </div>
  );
}
