"use client";

import { useEffect, useState } from "react";

const MESSAGES = [
  "Done! 1 Einspruch deadline found, added to your calendar.",
  "Rundfunkbeitrag: pay €63.08 by 30 Nov. GiroCode ready.",
  "Widerspruch drafted in German. English copy attached.",
  "ABH appointment: bring passport, photo and 3 payslips.",
];

/** A pixel-bordered speech bubble that types status messages, one after another. */
export default function TypingPrompt({ className = "" }: { className?: string }) {
  const [index, setIndex] = useState(0);
  const [length, setLength] = useState(0);

  useEffect(() => {
    const full = MESSAGES[index];
    const done = length >= full.length;
    const t = setTimeout(
      () => {
        if (done) {
          setLength(0);
          setIndex((index + 1) % MESSAGES.length);
        } else {
          setLength(length + 1);
        }
      },
      done ? 2400 : 35,
    );
    return () => clearTimeout(t);
  }, [index, length]);

  return (
    <div className={`relative ${className}`}>
      <div className="pixel-box w-64 px-3 py-2.5 font-mono text-[12px] leading-snug">
        <p className="min-h-[2.8em]">
          {MESSAGES[index].slice(0, length)}
          <span className="animate-blink ml-0.5 inline-block h-3 w-2 translate-y-0.5 bg-ink" />
        </p>
      </div>
      {/* stepped pixel tail */}
      <span className="absolute -bottom-[10px] left-6 h-[10px] w-[10px] border-x-2 border-b-2 border-ink bg-paper-2" />
      <span className="absolute -bottom-[16px] left-4 h-[6px] w-[6px] bg-ink" />
    </div>
  );
}
