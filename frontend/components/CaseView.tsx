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
  if (!c) return <p className="text-ink/55">Loading…</p>;

  const setStatus = async (s: string) => setCase(await api.setStatus(c.id, s));
  const remove = async () => {
    if (!confirm("Delete this case and all its letters? This can't be undone.")) return;
    await api.deleteCase(c.id);
    router.push("/cases");
  };

  return (
    <div className="space-y-5">
      <Link href="/cases" className="text-sm text-ink/55 hover:underline">
        ← All cases
      </Link>
      <section className="card space-y-2">
        <h1 className="text-3xl font-medium leading-tight sm:text-4xl">{c.title}</h1>
        <p className="text-ink/55">
          {c.sender_name}
          {c.reference && <> · <span className="font-mono">{c.reference}</span></>}
        </p>
        <div className="flex flex-wrap gap-1 pt-2">
          {ORDER.map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`border px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] ${c.status === s ? "border-ink bg-ink text-paper-2" : "border-ink/20 text-ink/65 hover:border-ink/50"}`}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
        </div>
        {c.needs_follow_up && (
          <p className="border border-accent/60 bg-accent/5 px-3 py-2 text-sm text-ink/80">
            You&apos;ve been waiting more than 6 weeks. Open the latest letter and choose &quot;Ask about the status of your case&quot;.
          </p>
        )}
      </section>

      <section className="card space-y-2">
        <h2 className="mono-label">Letters</h2>
        {c.letters?.map((l) => (
          <Link key={l.id} href={`/letters/${l.id}`} className="flex justify-between px-2 py-2 hover:bg-ink/5">
            <span>{l.title}</span>
            <span className="text-sm text-ink/55">{deDate(l.letter_date)}</span>
          </Link>
        ))}
      </section>

      <section className="card space-y-2">
        <h2 className="mono-label">Timeline</h2>
        <ol className="relative space-y-3 border-l border-line pl-4">
          {c.timeline?.map((e, i) => (
            <li key={i} className="text-sm">
              <span className="absolute -left-1.5 mt-1 h-3 w-3 bg-accent" />
              <span className="block">{e.text}</span>
              <span className="text-xs text-ink/55">{new Date(e.at).toLocaleString("en-GB")}</span>
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
