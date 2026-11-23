"use client";

import { useEffect, useState } from "react";
import { CornerTicks } from "@/components/Frame";

const PROMPTS = [
  "Explain my Steuerbescheid and put the deadline in my calendar",
  "When do I have to object to the Rundfunkbeitrag letter?",
  "Draft a Widerspruch in German for me",
  "What documents do I bring to the Ausländerbehörde?",
];

/** A terminal-style box that types example requests, one after another. */
export default function TypingPrompt() {
  const [index, setIndex] = useState(0);
  const [length, setLength] = useState(0);

  useEffect(() => {
    const full = PROMPTS[index];
    const done = length >= full.length;
    const t = setTimeout(
      () => {
        if (done) {
          setLength(0);
          setIndex((index + 1) % PROMPTS.length);
        } else {
          setLength(length + 1);
        }
      },
      done ? 2200 : 38,
    );
    return () => clearTimeout(t);
  }, [index, length]);

  return (
    <div className="relative max-w-sm border border-line bg-paper-2/70 p-4 backdrop-blur-sm">
      <CornerTicks />
      <div className="mono-label mb-2 flex items-center justify-between">
        <span>›_ Ask about a letter</span>
        <span className="text-accent">●</span>
      </div>
      <p className="min-h-[3.2em] font-mono text-[12px] uppercase leading-relaxed tracking-[0.08em] text-ink/85">
        {PROMPTS[index].slice(0, length)}
        <span className="animate-blink ml-0.5 inline-block h-3.5 w-2 translate-y-0.5 bg-ink" />
      </p>
    </div>
  );
}
