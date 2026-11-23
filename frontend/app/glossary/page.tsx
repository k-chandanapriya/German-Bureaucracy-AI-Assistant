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
      <h1 className="text-2xl font-bold">Amtsdeutsch glossary</h1>
      <input className="input" placeholder="Search, e.g. Bescheid" value={q} onChange={(e) => setQ(e.target.value)} />
      {error && <p className="text-red-700">{error}</p>}
      <dl className="card divide-y divide-stone-100">
        {entries.map(([term, def]) => (
          <div key={term} className="py-3">
            <dt className="font-semibold">{term}</dt>
            <dd className="text-stone-600">{def}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
