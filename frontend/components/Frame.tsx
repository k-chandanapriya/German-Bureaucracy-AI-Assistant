/** Corner tick marks, like crop marks on a technical drawing. */
export function CornerTicks({ className = "border-ink/50" }: { className?: string }) {
  const base = `pointer-events-none absolute h-2.5 w-2.5 ${className}`;
  return (
    <>
      <span className={`${base} -left-px -top-px border-l border-t`} />
      <span className={`${base} -right-px -top-px border-r border-t`} />
      <span className={`${base} -bottom-px -left-px border-b border-l`} />
      <span className={`${base} -bottom-px -right-px border-b border-r`} />
    </>
  );
}

/** A section with a numbered mono label: "01 / Upload". */
export function SectionLabel({ index, children }: { index: string; children: React.ReactNode }) {
  return (
    <div className="mono-label mb-4 flex items-center gap-3">
      <span className="text-accent">{index}</span>
      <span className="h-px w-6 bg-ink/25" />
      <span>{children}</span>
    </div>
  );
}
