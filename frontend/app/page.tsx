"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import BundeslandSelect, { useBundesland } from "@/components/BundeslandSelect";
import { api, type Meta, type ReadingJob } from "@/lib/api";

const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";

export default function Home() {
  const router = useRouter();
  const [meta, setMeta] = useState<Meta | null>(null);
  const [land, setLand] = useBundesland();
  const [files, setFiles] = useState<File[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [job, setJob] = useState<ReadingJob | null>(null);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.meta().then(setMeta).catch((e) => setError(e.message));
  }, []);

  const addFiles = (list: FileList | null) => {
    if (!list) return;
    const accepted = Array.from(list).filter((f) => ACCEPT.split(",").includes(f.type));
    if (accepted.length < list.length) setError("Only JPG, PNG, WEBP and PDF files are supported.");
    setFiles((prev) => [...prev, ...accepted]);
  };

  const run = async (label: string, fn: () => Promise<{ letter_id: number }>) => {
    setBusy(label);
    setError(null);
    try {
      const card = await fn();
      router.push(`/letters/${card.letter_id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(null);
    }
  };

  const readLetter = async () => {
    setBusy("upload");
    setError(null);
    try {
      let state = await api.startReading(files, land);
      setJob(state);
      while (state.status === "queued" || state.status === "running") {
        await new Promise((r) => setTimeout(r, 1500));
        state = await api.job(state.id);
        setJob(state);
      }
      if (state.status === "error" || !state.result) throw new Error(state.error ?? "Reading failed");
      router.push(`/letters/${state.result.letter_id}`);
    } catch (e) {
      setError((e as Error).message);
      setBusy(null);
      setJob(null);
    }
  };

  return (
    <div className="space-y-8">
      <section className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Got a letter from a German authority?</h1>
        <p className="max-w-2xl text-lg text-stone-600">
          Take a photo. We tell you what it means, what you have to do and by when. Then we put the deadline in
          your calendar and draft the German reply.
        </p>
      </section>

      <section className="card space-y-4">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            addFiles(e.dataTransfer.files);
          }}
          onClick={() => input.current?.click()}
          className={`cursor-pointer rounded-xl border-2 border-dashed p-10 text-center transition ${
            dragging ? "border-amber-500 bg-amber-50" : "border-stone-300 hover:border-stone-400"
          }`}
        >
          <div className="text-4xl">📸</div>
          <p className="mt-2 font-medium">Drop photos or a PDF here, or click to choose</p>
          <p className="text-sm text-stone-500">Several pages? Add them all, in order.</p>
          <input
            ref={input}
            type="file"
            accept={ACCEPT}
            multiple
            capture="environment"
            className="hidden"
            onChange={(e) => addFiles(e.target.files)}
          />
        </div>

        {files.length > 0 && (
          <ul className="space-y-1 text-sm">
            {files.map((f, i) => (
              <li key={i} className="flex items-center justify-between rounded-md bg-stone-100 px-3 py-1.5">
                <span>
                  Page {i + 1}: {f.name}
                </span>
                <button className="text-stone-500 hover:text-red-600" onClick={() => setFiles(files.filter((_, j) => j !== i))}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
          {meta && <BundeslandSelect value={land} onChange={setLand} options={meta.bundeslaender} />}
          <button
            className="btn-primary h-10"
            disabled={!files.length || !!busy}
            onClick={readLetter}
          >
            {busy === "upload" ? "Reading your letter…" : "Explain my letter"}
          </button>
        </div>
        {job && busy === "upload" && (
          <div className="flex items-center gap-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-900" aria-live="polite">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-amber-300 border-t-amber-700" />
            <span className="flex-1">{job.stage}…</span>
            <span className="tabular-nums text-amber-700">{job.elapsed_s}s</span>
          </div>
        )}
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        <p className="text-xs text-stone-500">
          {meta?.ai_provider === "ollama"
            ? `Letters are read by a local AI model (${meta.ai_model}) on this computer. Nothing is sent to the internet. Reading can take a minute.`
            : "Letters are read by Claude under a data-processing agreement; only the extracted data is stored on this server."}{" "}
          You can delete a case at any time.
        </p>
      </section>

      {meta && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">No letter at hand? Try a sample</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {meta.samples.map((s) => (
              <button
                key={s.id}
                onClick={() => run(s.id, () => api.sample(s.id, land))}
                disabled={!!busy}
                className="card text-left transition hover:border-stone-400 disabled:opacity-60"
              >
                <div className="font-medium">{busy === s.id ? "Opening…" : s.label}</div>
                <p className="mt-2 line-clamp-4 font-mono text-xs text-stone-500">{s.preview}</p>
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="grid gap-4 sm:grid-cols-3">
        {[
          ["📅", "Deadlines you can trust", "Computed by code, not AI: 4-day notification rule, month ends, weekends and your state's holidays."],
          ["✍️", "Replies in correct German", "Reviewed templates for Einspruch, Widerspruch, extensions and more, as a DIN 5008 PDF."],
          ["🗂️", "Everything in one place", "Reminders link to the original case. See what's open and what you're waiting for."],
        ].map(([icon, title, text]) => (
          <div key={title} className="space-y-1">
            <div className="text-2xl">{icon}</div>
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-stone-600">{text}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
