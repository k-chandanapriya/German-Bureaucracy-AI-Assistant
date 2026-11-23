"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, STATUS_LABELS, type CaseSummary } from "@/lib/api";

const SENDER_ICON: Record<string, string> = {
  finanzamt: "🧾",
  auslaenderbehoerde: "🛂",
  beitragsservice: "📺",
  other: "✉️",
};

export default function CasesPage() {
  const [cases, setCases] = useState<CaseSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.cases().then(setCases).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-700">{error}</p>;
  if (!cases) return <p className="text-stone-500">Loading…</p>;

  const open = cases.filter((c) => c.status !== "closed");
  const closed = cases.filter((c) => c.status === "closed");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">My cases</h1>
      {cases.length === 0 && (
        <p className="card text-stone-600">
          No letters yet. <Link className="underline" href="/">Scan your first letter</Link>.
        </p>
      )}
      {[
        ["Open", open],
        ["Closed", closed],
      ].map(([title, list]) =>
        (list as CaseSummary[]).length ? (
          <section key={title as string} className="space-y-2">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">{title as string}</h2>
            {(list as CaseSummary[]).map((c) => (
              <Link key={c.id} href={`/cases/${c.id}`} className="card flex items-center gap-4 transition hover:border-stone-400">
                <span className="text-2xl">{SENDER_ICON[c.sender_category] ?? "✉️"}</span>
                <span className="flex-1">
                  <span className="block font-medium">{c.title}</span>
                  <span className="text-sm text-stone-500">
                    {c.sender_name} · {c.letter_count} letter{c.letter_count > 1 ? "s" : ""}
                    {c.reference && ` · ${c.reference}`}
                  </span>
                  {c.needs_follow_up && (
                    <span className="mt-1 block text-sm text-amber-700">No answer for 6 weeks: send a Sachstandsanfrage?</span>
                  )}
                </span>
                <span className="text-right text-sm">
                  <span className="block rounded-full bg-stone-100 px-2.5 py-0.5">{STATUS_LABELS[c.status] ?? c.status}</span>
                  {c.next_deadline && <span className="mt-1 block text-stone-500">next: {c.next_deadline.due_date_display}</span>}
                </span>
              </Link>
            ))}
          </section>
        ) : null,
      )}
    </div>
  );
}
