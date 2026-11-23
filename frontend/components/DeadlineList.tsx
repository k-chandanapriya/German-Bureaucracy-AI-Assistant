"use client";

import { useState } from "react";
import type { Deadline } from "@/lib/api";

const TYPE_TAG: Record<Deadline["type"], string> = {
  appeal: "Objection",
  payment: "Payment",
  action: "Action",
  appointment: "Appointment",
};

function urgency(days: number) {
  if (days < 0) return "border-ink/20 text-ink/50";
  if (days <= 7) return "border-red-500 text-red-700";
  if (days <= 21) return "border-accent text-accent";
  return "border-emerald-600 text-emerald-700";
}

function daysText(days: number) {
  if (days < 0) return `${-days} days ago`;
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  return `in ${days} days`;
}

export default function DeadlineList({ deadlines }: { deadlines: Deadline[] }) {
  const [open, setOpen] = useState<number | null>(0);
  if (!deadlines.length) return <p className="text-sm text-ink/55">No deadlines in this letter.</p>;
  return (
    <ul className="space-y-2">
      {deadlines.map((d, i) => (
        <li key={i} className="border border-line bg-paper-2/60">
          <button className="flex w-full items-center gap-3 p-3 text-left" onClick={() => setOpen(open === i ? null : i)}>
            <span className="w-24 shrink-0 font-mono text-[10px] uppercase tracking-[0.14em] text-accent">{TYPE_TAG[d.type]}</span>
            <span className="flex-1">
              <span className="block text-sm text-ink/70">{d.label}</span>
              <span className="text-2xl font-light tracking-tight">{d.due_date_display}</span>
            </span>
            <span className={`border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.12em] ${urgency(d.days_left)}`}>{daysText(d.days_left)}</span>
            <span className="text-ink/40">{open === i ? "▲" : "▼"}</span>
          </button>
          {open === i && (
            <div className="border-t border-line bg-paper p-3 text-sm">
              <p className="label">How we calculated it</p>
              <ol className="list-decimal space-y-1 pl-5 font-mono text-xs">
                {d.steps.map((s, j) => (
                  <li key={j}>{s}</li>
                ))}
              </ol>
              {d.warnings.map((w, j) => (
                <p key={j} className="mt-2 text-xs text-amber-800">
                  ⚠ {w}
                </p>
              ))}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
