"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, deDate, STATUS_LABELS, type CaseSummary } from "@/lib/api";

const ORDER = ["new", "understood", "action_needed", "replied", "waiting", "closed"];

export default function CaseView() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [c, setCase] = useState<CaseSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.case(id).then(setCase).catch((e) => setError(e.message));
  }, [id]);

  if (error) return <p className="text-red-700">{error}</p>;
  if (!c) return <p className="text-stone-500">Loading…</p>;

  const setStatus = async (s: string) => setCase(await api.setStatus(c.id, s));
  const remove = async () => {
    if (!confirm("Delete this case and all its letters? This can't be undone.")) return;
    await api.deleteCase(c.id);
    router.push("/cases");
  };

  return (
    <div className="space-y-5">
      <Link href="/cases" className="text-sm text-stone-500 hover:underline">
        ← All cases
      </Link>
      <section className="card space-y-2">
        <h1 className="text-2xl font-bold">{c.title}</h1>
        <p className="text-stone-500">
          {c.sender_name}
          {c.reference && <> · <span className="font-mono">{c.reference}</span></>}
        </p>
        <div className="flex flex-wrap gap-1 pt-2">
          {ORDER.map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`rounded-full px-3 py-1 text-sm ${c.status === s ? "bg-stone-900 text-white" : "bg-stone-100 text-stone-600 hover:bg-stone-200"}`}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
        {c.needs_follow_up && (
          <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            You&apos;ve been waiting more than 6 weeks. Open the latest letter and choose &quot;Ask about the status of your case&quot;.
          </p>
        )}
      </section>

      <section className="card space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">Letters</h2>
        {c.letters?.map((l) => (
          <Link key={l.id} href={`/letters/${l.id}`} className="flex justify-between rounded-lg px-2 py-2 hover:bg-stone-50">
            <span>{l.title}</span>
            <span className="text-sm text-stone-500">{deDate(l.letter_date)}</span>
          </Link>
        ))}
      </section>

      <section className="card space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-stone-500">Timeline</h2>
        <ol className="relative space-y-3 border-l border-stone-200 pl-4">
          {c.timeline?.map((e, i) => (
            <li key={i} className="text-sm">
              <span className="absolute -left-1.5 mt-1 h-3 w-3 rounded-full bg-stone-300" />
              <span className="block">{e.text}</span>
              <span className="text-xs text-stone-500">{new Date(e.at).toLocaleString("en-GB")}</span>
            </li>
          ))}
        </ol>
      </section>

      <button onClick={remove} className="text-sm text-red-700 hover:underline">
        Delete case and letters
      </button>
    </div>
  );
}
