"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import BundeslandSelect, { useBundesland } from "@/components/BundeslandSelect";
import { CornerTicks, SectionLabel } from "@/components/Frame";
import MailBot from "@/components/MailBot";
import TypingPrompt from "@/components/TypingPrompt";
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
    <div className="space-y-24">
      {/* ---------------- Hero ---------------- */}
      <section className="relative -mt-4 grid min-h-[640px] items-center gap-10 lg:grid-cols-[1.05fr_1fr]">
        <div className="animate-fade-up relative z-10 space-y-10">
          <TypingPrompt />
          <div>
            <p className="mono-label mb-4">Understand every</p>
            <h1 className="space-y-2 text-5xl font-light tracking-tight sm:text-6xl lg:text-7xl">
              <span className="framed">German</span>
              <br />
              <span className="framed">Letters</span>
            </h1>
          </div>
          <p className="max-w-md text-[15px] leading-relaxed text-ink/70">
            Take a photo of any letter from the Finanzamt, Ausländerbehörde or Beitragsservice. Amtspost tells you what it
            means, what you have to do and by when, then puts the deadline in your calendar and drafts the German reply.
          </p>
          <div className="flex flex-wrap gap-3">
            <a href="#scan" className="btn-primary">
              Scan a letter ↓
            </a>
            <a href="#samples" className="btn-secondary">
              Try a sample
            </a>
          </div>
        </div>

        <div className="relative pt-6">
          <div className="flex justify-center lg:justify-start lg:pl-6">
            <MailBot className="w-[78%] max-w-[340px]" />
          </div>
          {/* callouts linked by thin lines */}
          <ul className="absolute right-0 top-12 hidden sm:block">
            {["Deadlines", "German replies", "Calendar sync", "Case tracking"].map((t, i) => (
              <li key={t} className="flex items-center justify-end gap-3">
                <span className={`h-px ${i === 0 ? "w-28" : "w-14"} bg-ink/30`} />
                <span className="mono-label border-b border-line py-1.5 text-ink/75">{t}</span>
              </li>
            ))}
          </ul>
          <div className="mt-6 flex items-end justify-end gap-4">
            <p className="max-w-[230px] text-[13px] leading-snug text-ink/70">
              Your personal guide to official German letters, explained in plain English.
            </p>
            <a
              href="#scan"
              aria-label="Scroll to upload"
              className="grid h-9 w-9 shrink-0 place-items-center border border-ink/30 text-ink/70 hover:bg-ink hover:text-paper-2"
            >
              ↓
            </a>
          </div>
        </div>
      </section>

      {/* ---------------- Upload ---------------- */}
      <section id="scan" className="scroll-mt-24">
        <SectionLabel index="01">Upload your letter</SectionLabel>
        <div className="card space-y-5 p-6 sm:p-8">
          <CornerTicks />
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
            className={`cursor-pointer border border-dashed p-12 text-center transition ${
              dragging ? "border-accent bg-accent/5" : "border-ink/25 hover:border-ink/60"
            }`}
          >
            <div className="accent-gradient mx-auto grid h-12 w-12 place-items-center rounded-xl text-xl text-white">↑</div>
            <p className="mt-4 text-lg font-light">Drop photos or a PDF here, or click to choose</p>
            <p className="mono-label mt-2">JPG · PNG · WEBP · PDF — several pages? add them in order</p>
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
            <ul className="divide-y divide-line border border-line">
              {files.map((f, i) => (
                <li key={i} className="flex items-center justify-between px-3 py-2 text-sm">
                  <span>
                    <span className="mono-label mr-3 text-accent">P{String(i + 1).padStart(2, "0")}</span>
                    {f.name}
                  </span>
                  <button className="mono-label hover:text-red-700" onClick={() => setFiles(files.filter((_, j) => j !== i))}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
            {meta && <BundeslandSelect value={land} onChange={setLand} options={meta.bundeslaender} />}
            <button className="btn-primary h-10 px-6" disabled={!files.length || !!busy} onClick={readLetter}>
              {busy === "upload" ? "Reading…" : "Explain my letter →"}
            </button>
          </div>

          {job && busy === "upload" && (
            <div className="flex items-center gap-3 border border-accent/40 bg-accent/5 px-4 py-3" aria-live="polite">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-accent/30 border-t-accent" />
              <span className="mono-label flex-1 text-ink/80">{job.stage}…</span>
              <span className="font-mono text-xs tabular-nums text-accent">{job.elapsed_s}s</span>
            </div>
          )}
          {error && <p className="border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
          <p className="mono-label normal-case tracking-normal text-ink/50">
            {meta?.ai_provider === "ollama"
              ? `Read by a local AI model (${meta.ai_model}) on this computer. Nothing is sent to the internet. Reading takes about a minute per page.`
              : "Read by Claude under a data-processing agreement; only the extracted data is stored on this server."}{" "}
            You can delete a case at any time.
          </p>
        </div>
      </section>

      {/* ---------------- Samples ---------------- */}
      {meta && (
        <section id="samples" className="scroll-mt-24">
          <SectionLabel index="02">No letter at hand? Try a sample</SectionLabel>
          <div className="grid gap-px border border-line bg-line sm:grid-cols-3">
            {meta.samples.map((s, i) => (
              <button
                key={s.id}
                onClick={() => run(s.id, () => api.sample(s.id, land))}
                disabled={!!busy}
                className="group relative flex flex-col bg-paper-2 p-6 text-left transition hover:bg-white disabled:opacity-60"
              >
                <div className="mono-label mb-3 flex justify-between">
                  <span>Sample {String(i + 1).padStart(2, "0")}</span>
                  <span className="text-ink/40 transition group-hover:text-accent">↗</span>
                </div>
                <div className="text-lg font-light">{busy === s.id ? "Opening…" : s.label}</div>
                <p className="mt-3 line-clamp-4 font-mono text-[11px] leading-relaxed text-ink/50">{s.preview}</p>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* ---------------- Why ---------------- */}
      <section>
        <SectionLabel index="03">Why Amtspost</SectionLabel>
        <div className="grid gap-px border border-line bg-line sm:grid-cols-3">
          {[
            ["Deadlines you can trust", "Computed by code, not AI: the 4-day notification rule, month ends, weekends and your state's public holidays, with every step shown."],
            ["Replies in correct German", "Templates for Einspruch, Widerspruch, extensions and more, with an English translation, as a DIN 5008 PDF."],
            ["Everything in one place", "Reminder letters link to the original case. See what's open, what's due and what you're waiting for."],
          ].map(([title, text], i) => (
            <div key={title} className="bg-paper-2 p-6">
              <div className="mono-label mb-6 text-accent">{String(i + 1).padStart(2, "0")}</div>
              <h3 className="text-xl font-light">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink/65">{text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
