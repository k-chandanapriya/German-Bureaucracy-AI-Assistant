"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function GlossaryPage() {
  const [terms, setTerms] = useState<Record<string, string>>({});
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.glossary().then(setTerms).catch((e) => setError(e.message));
  }, []);

  const entries = Object.entries(terms)
    .filter(([t, d]) => (t + d).toLowerCase().includes(q.toLowerCase()))
    .sort(([a], [b]) => a.localeCompare(b, "de"));

  return (
    <div className="space-y-5">
      <div>
        <p className="mono-label mb-3">Amtspost / Glossary</p>
        <h1 className="text-4xl font-light tracking-tight sm:text-5xl">
          <span className="framed">Amtsdeutsch</span> glossary
        </h1>
      </div>
      <input className="input" placeholder="Search, e.g. Bescheid" value={q} onChange={(e) => setQ(e.target.value)} />
      {error && <p className="text-red-700">{error}</p>}
      <dl className="card divide-y divide-line">
        {entries.map(([term, def]) => (
          <div key={term} className="py-3">
            <dt className="font-mono text-[13px] uppercase tracking-[0.08em] text-accent">{term}</dt>
            <dd className="text-ink/65">{def}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
