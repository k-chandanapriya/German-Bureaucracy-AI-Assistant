"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/#scan", label: "Scan" },
  { href: "/cases", label: "My cases" },
  { href: "/deadline", label: "Deadlines" },
  { href: "/glossary", label: "Glossary" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <header className="sticky top-0 z-40 bg-paper/90 backdrop-blur">
      <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 sm:px-6">
        <Link href="/" className="font-pixel text-[15px] font-bold tracking-wide">
          Briefly
        </Link>
        <div className="flex items-center gap-4 sm:gap-7">
          {LINKS.map((l) => {
            const active = l.href !== "/#scan" && path.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`font-mono text-[12px] underline-offset-4 transition hover:underline ${
                  active ? "text-ink underline" : "text-ink/70"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
