"use client";

import { useEffect, useState } from "react";
import BundeslandSelect, { useBundesland } from "@/components/BundeslandSelect";
import DeadlineList from "@/components/DeadlineList";
import { api, type Deadline } from "@/lib/api";

const BASES = [
  ["AO", "Tax office (Abgabenordnung)"],
  ["VwVfG", "Other authorities: immigration, broadcasting fee (VwVfG)"],
  ["SGB X", "Social benefits: Jobcenter, Krankenkasse, Elterngeld (SGB X)"],
];

export default function DeadlinePage() {
  const [lands, setLands] = useState<Record<string, string>>({});
  const [land, setLand] = useBundesland();
  const [form, setForm] = useState({
    letter_date: "",
    received_date: "",
    legal_basis: "AO",
    period_length: "1",
    period_unit: "months",
  });
  const [result, setResult] = useState<Deadline | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.meta().then((m) => setLands(m.bundeslaender)).catch((e) => setError(e.message));
  }, []);

  const compute = async () => {
    setError(null);
    try {
      const r = await api.computeDeadline({
        bundesland: land,
        letter_date: form.letter_date || null,
        received_date: form.received_date || null,
        delivery: form.received_date ? "known" : "post",
        legal_basis: form.legal_basis,
        period_length: Number(form.period_length),
        period_unit: form.period_unit,
        label: "Your deadline",
      });
      setResult({ ...r, type: "appeal" });
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm({ ...form, [k]: e.target.value });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold">Deadline calculator</h1>
        <p className="text-stone-600">
          &quot;One month after notification&quot; — but when exactly? Enter the date on the letter and we apply the German rules step by step.
        </p>
      </div>
      <section className="card grid gap-4 sm:grid-cols-2">
        <label>
          <span className="label">Date printed on the letter</span>
          <input type="date" className="input" value={form.letter_date} onChange={set("letter_date")} />
        </label>
        <label>
          <span className="label">Or: date you actually received it (optional)</span>
          <input type="date" className="input" value={form.received_date} onChange={set("received_date")} />
        </label>
        <label className="sm:col-span-2">
          <span className="label">Who sent it?</span>
          <select className="input" value={form.legal_basis} onChange={set("legal_basis")}>
            {BASES.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span className="label">Period in the letter</span>
          <div className="flex gap-2">
            <input type="number" min={1} className="input w-24" value={form.period_length} onChange={set("period_length")} />
            <select className="input" value={form.period_unit} onChange={set("period_unit")}>
              <option value="days">days</option>
              <option value="weeks">weeks</option>
              <option value="months">months</option>
            </select>
          </div>
        </label>
        {Object.keys(lands).length > 0 && <BundeslandSelect value={land} onChange={setLand} options={lands} />}
        <div className="sm:col-span-2">
          <button className="btn-primary" onClick={compute} disabled={!form.letter_date && !form.received_date}>
            Calculate
          </button>
        </div>
        {error && <p className="text-sm text-red-700 sm:col-span-2">{error}</p>}
      </section>
      {result && (
        <section className="card">
          <DeadlineList deadlines={[result]} />
        </section>
      )}
    </div>
  );
}
