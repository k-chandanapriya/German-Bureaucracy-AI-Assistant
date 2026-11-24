"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, STATUS_LABELS, type CaseSummary } from "@/lib/api";

const SENDER_TAG: Record<string, string> = {
  finanzamt: "FA",
  auslaenderbehoerde: "ABH",
  beitragsservice: "RB",
  other: "—",
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.cases().then(setCases).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-700">{error}</p>;
  if (!cases) return <p className="text-ink/55">Loading…</p>;

  const open = cases.filter((c) => c.status !== "closed");
  const closed = cases.filter((c) => c.status === "closed");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-pixel text-4xl font-bold uppercase sm:text-5xl">My cases</h1>
        <p className="mt-2 text-[13px] text-ink/65">Every letter, grouped by reference number, with its next deadline.</p>
      </div>
      {cases.length === 0 && (
        <p className="card text-ink/65">
          No letters yet. <Link className="underline" href="/">Scan your first letter</Link>.
        </p>
      )}
      {[
        ["Open", open],
        ["Closed", closed],
      ].map(([title, list]) =>
        (list as CaseSummary[]).length ? (
          <section key={title as string} className="space-y-2">
            <h2 className="mono-label">{title as string}</h2>
            {(list as CaseSummary[]).map((c) => (
              <Link key={c.id} href={`/case?id=${c.id}`} className="card flex items-center gap-4 transition hover:border-ink/50">
                <span className="grid h-11 w-11 shrink-0 place-items-center border border-accent/60 font-mono text-[11px] tracking-wider text-accent">
                  {SENDER_TAG[c.sender_category] ?? "—"}
                </span>
                <span className="flex-1">
                  <span className="block font-medium">{c.title}</span>
                  <span className="text-sm text-ink/55">
                    {c.sender_name} · {c.letter_count} letter{c.letter_count > 1 ? "s" : ""}
                    {c.reference && ` · ${c.reference}`}
                  </span>
                  {c.needs_follow_up && (
                    <span className="mt-1 block text-sm text-amber-700">No answer for 6 weeks: send a Sachstandsanfrage?</span>
                  )}
                </span>
                <span className="text-right text-sm">
                  <span className="mono-label inline-block border border-ink/25 px-2 py-0.5 text-ink/75">{STATUS_LABELS[c.status] ?? c.status}</span>
                  {c.next_deadline && <span className="mono-label mt-2 block normal-case tracking-normal">Next: {c.next_deadline.due_date_display}</span>}
                </span>
              </Link>
            ))}
          </section>
        ) : null,
      )}
    </div>
  );
}
