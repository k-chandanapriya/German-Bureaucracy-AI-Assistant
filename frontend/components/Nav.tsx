"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/cases", label: "My cases", short: "Cases" },
  { href: "/deadline", label: "Deadline calculator", short: "Deadlines" },
  { href: "/glossary", label: "Glossary", short: "Glossary" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/85 backdrop-blur">
      <nav className="mx-auto flex h-14 max-w-6xl items-stretch px-4 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 pr-6 font-mono text-[13px] font-medium uppercase tracking-[0.12em]">
          <span className="accent-gradient grid h-6 w-6 place-items-center rounded-[5px] text-[11px] text-white">✉</span>
          Amtspost
        </Link>
        <div className="hidden flex-1 items-stretch border-l border-line sm:flex">
          {LINKS.map((l) => {
            const active = path.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`flex items-center border-r border-line px-5 font-mono text-[11px] uppercase tracking-[0.14em] transition ${
                  active ? "bg-ink text-paper-2" : "text-ink/65 hover:bg-ink/5 hover:text-ink"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
        <div className="ml-auto flex items-center gap-3">
          <div className="flex items-center gap-1 sm:hidden">
            {LINKS.map((l) => (
              <Link key={l.href} href={l.href} className="px-2 font-mono text-[10px] uppercase tracking-wider text-ink/65">
                {l.short}
              </Link>
            ))}
          </div>
          <Link href="/#scan" className="btn-accent hidden sm:inline-flex">
            Scan a letter ↗
          </Link>
        </div>
      </nav>
    </header>
  );
}
