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
        <h1 className="font-pixel text-4xl font-bold uppercase sm:text-5xl">Amtsdeutsch glossary</h1>
        <p className="mt-2 text-[13px] text-ink/65">The words official letters use, in plain English.</p>
      </div>
      <input className="input" placeholder="Search, e.g. Bescheid" value={q} onChange={(e) => setQ(e.target.value)} />
      {error && <p className="text-red-700">{error}</p>}
      <dl className="card divide-y divide-line">
        {entries.map(([term, def]) => (
          <div key={term} className="py-3">
            <dt className="font-pixel text-[15px] font-bold">{term}</dt>
            <dd className="text-ink/65">{def}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
