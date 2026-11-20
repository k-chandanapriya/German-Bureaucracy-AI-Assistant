"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Scan a letter" },
  { href: "/cases", label: "My cases" },
  { href: "/deadline", label: "Deadline calculator" },
  { href: "/glossary", label: "Glossary" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <header className="border-b border-stone-200 bg-white">
      <nav className="mx-auto flex max-w-4xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-amber-400 text-lg">✉</span>
          Amtspost
        </Link>
        <div className="flex flex-wrap gap-1 text-sm">
          {LINKS.map((l) => {
            const active = l.href === "/" ? path === "/" : path.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded-md px-3 py-1.5 ${active ? "bg-stone-900 text-white" : "text-stone-600 hover:bg-stone-100"}`}
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
