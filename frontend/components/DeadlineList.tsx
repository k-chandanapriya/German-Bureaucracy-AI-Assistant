"use client";

import { useState } from "react";
import type { Deadline } from "@/lib/api";

const TYPE_ICON: Record<Deadline["type"], string> = {
  appeal: "⚖️",
  payment: "💶",
  action: "✅",
  appointment: "📍",
};

function urgency(days: number) {
  if (days < 0) return "bg-stone-200 text-stone-600";
  if (days <= 7) return "bg-red-100 text-red-800";
  if (days <= 21) return "bg-amber-100 text-amber-800";
  return "bg-emerald-100 text-emerald-800";
}

function daysText(days: number) {
  if (days < 0) return `${-days} days ago`;
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  return `in ${days} days`;
}

export default function DeadlineList({ deadlines }: { deadlines: Deadline[] }) {
  const [open, setOpen] = useState<number | null>(0);
  if (!deadlines.length) return <p className="text-sm text-stone-500">No deadlines in this letter.</p>;
  return (
    <ul className="space-y-2">
      {deadlines.map((d, i) => (
        <li key={i} className="rounded-xl border border-stone-200">
          <button className="flex w-full items-center gap-3 p-3 text-left" onClick={() => setOpen(open === i ? null : i)}>
            <span className="text-xl">{TYPE_ICON[d.type]}</span>
            <span className="flex-1">
              <span className="block font-medium">{d.label}</span>
              <span className="text-lg font-semibold">{d.due_date_display}</span>
            </span>
            <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${urgency(d.days_left)}`}>{daysText(d.days_left)}</span>
            <span className="text-stone-400">{open === i ? "▲" : "▼"}</span>
          </button>
          {open === i && (
            <div className="border-t border-stone-100 bg-stone-50 p-3 text-sm">
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
