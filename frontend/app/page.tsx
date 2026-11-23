"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import BundeslandSelect, { useBundesland } from "@/components/BundeslandSelect";
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
    <div className="space-y-20">
      {/* ---------------- Hero ---------------- */}
      <section className="relative -mx-4 -mt-10 overflow-hidden px-4 pb-6 pt-10 sm:-mx-6 sm:px-6">
        <div className="grid items-center gap-6 lg:grid-cols-2">
          <div className="animate-fade-up relative z-10 space-y-7 py-8">
            <h1 className="font-pixel text-[48px] font-bold uppercase leading-[0.92] sm:text-[68px] xl:text-[80px]">
              Amtspost
              <br />
              AI Agent
            </h1>
            <p className="max-w-sm text-[13px] leading-relaxed text-ink/80">
              Amtspost reads your German letters, works out the real deadline, puts it in your calendar and drafts the
              German reply.
            </p>
            <div className="flex flex-wrap items-center gap-6">
              <a href="#scan" className="btn-primary">
                Scan a letter
              </a>
              <a href="/deadline" className="btn-link">
                Try the deadline calculator ›
              </a>
            </div>
            <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-ink/70">
              <span>19 letter types</span>
              <span aria-hidden>•</span>
              <span>13 reply templates</span>
              <span aria-hidden>•</span>
              <span>16 Bundesländer</span>
            </p>
          </div>

          <div className="relative">
            <TypingPrompt className="absolute right-0 top-0 z-10 sm:right-6" />
            <MailBot className="mt-20 w-full scale-110 lg:origin-left" />
          </div>
        </div>
      </section>

      {/* ---------------- Upload ---------------- */}
      <section id="scan" className="scroll-mt-20">
        <div className="mb-5 flex items-end justify-between gap-4">
          <h2 className="font-pixel text-3xl font-bold uppercase sm:text-4xl">Scan a letter</h2>
          <span className="hidden text-[12px] text-ink/60 sm:block">Photo or PDF · several pages allowed</span>
        </div>
        <div className="card space-y-5 p-6 sm:p-8">
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
            className={`cursor-pointer border-2 border-dashed p-12 text-center transition ${
              dragging ? "border-ink bg-ink/5" : "border-ink/25 hover:border-ink/60"
            }`}
          >
            <div className="pixel-box mx-auto grid h-12 w-12 place-items-center font-pixel text-xl">↑</div>
            <p className="mt-5 text-[14px]">Drop photos or a PDF here, or click to choose</p>
            <p className="mt-1 text-[12px] text-ink/55">JPG · PNG · WEBP · PDF — several pages? Add them in order.</p>
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
                <li key={i} className="flex items-center justify-between px-3 py-2 text-[13px]">
                  <span>
                    <span className="mr-3 text-ink/50">p.{i + 1}</span>
                    {f.name}
                  </span>
                  <button className="text-[12px] text-ink/60 hover:text-red-700" onClick={() => setFiles(files.filter((_, j) => j !== i))}>
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
            {meta && <BundeslandSelect value={land} onChange={setLand} options={meta.bundeslaender} />}
            <button className="btn-primary h-10 px-6" disabled={!files.length || !!busy} onClick={readLetter}>
              {busy === "upload" ? "Reading…" : "Explain my letter ›"}
            </button>
          </div>

          {job && busy === "upload" && (
            <div className="pixel-box flex items-center gap-3 px-4 py-3" aria-live="polite">
              <span className="animate-blink inline-block h-3 w-2 bg-ink" />
              <span className="flex-1 text-[13px]">{job.stage}…</span>
              <span className="tabular-nums text-[12px] text-ink/60">{job.elapsed_s}s</span>
            </div>
          )}
          {error && <p className="border-2 border-red-600 bg-red-50 px-3 py-2 text-[13px] text-red-800">{error}</p>}
          <p className="text-[11px] leading-relaxed text-ink/55">
            {meta?.ai_provider === "ollama"
              ? `Read by a local AI model (${meta.ai_model}) on this computer. Nothing is sent to the internet. Reading takes about a minute per page.`
              : "Read by Claude under a data-processing agreement; only the extracted data is stored on this server."}{" "}
            You can delete a case at any time.
          </p>
        </div>
      </section>
    </div>
  );
}
