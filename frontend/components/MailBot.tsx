/**
 * Amtspost's mascot: a friendly letter drawn only with horizontal scanlines.
 * Shading comes from line thickness (light / mid / dark patterns), and a
 * stream of lines trails off to the right like a signal.
 */

// Deterministic "random" lengths so server and client render the same SVG.
const STREAM = Array.from({ length: 46 }, (_, i) => {
  const r = Math.abs(Math.sin(i * 12.9898) * 43758.5453) % 1;
  // Rounded: server and browser maths can differ in the last decimals.
  return { y: 38 + i * 6, len: Math.round(40 + r * 180), delay: (Math.round(r * 30) / 10).toFixed(1) };
});

export default function MailBot({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 560 360" className={className} aria-hidden>
      <defs>
        <pattern id="scan-l" width="6" height="6" patternUnits="userSpaceOnUse">
          <rect width="6" height="1.2" fill="#111" />
        </pattern>
        <pattern id="scan-m" width="6" height="6" patternUnits="userSpaceOnUse">
          <rect width="6" height="2.6" fill="#111" />
        </pattern>
        <pattern id="scan-d" width="6" height="6" patternUnits="userSpaceOnUse">
          <rect width="6" height="4.4" fill="#111" />
        </pattern>
      </defs>

      {/* signal lines streaming to the right */}
      <g opacity="0.9">
        {STREAM.map((s, i) => (
          <rect
            key={i}
            x={330}
            y={s.y}
            width={s.len}
            height={i % 3 === 0 ? 2.4 : 1.2}
            fill="#111"
            className="animate-stream"
            style={{ animationDelay: `${s.delay}s` }}
          />
        ))}
      </g>

      <g className="animate-float">
        {/* ground shadow */}
        <ellipse cx="190" cy="330" rx="150" ry="16" fill="url(#scan-m)" />

        {/* document sticking out */}
        <g transform="rotate(-7 190 90)">
          <rect x="112" y="24" width="150" height="128" fill="#f8f8f7" />
          <rect x="112" y="24" width="150" height="128" fill="url(#scan-l)" />
          <rect x="130" y="46" width="70" height="8" fill="#111" />
          <rect x="130" y="66" width="104" height="4" fill="#111" opacity="0.7" />
          <rect x="130" y="78" width="92" height="4" fill="#111" opacity="0.7" />
          <rect x="130" y="90" width="98" height="4" fill="#111" opacity="0.7" />
          <rect x="212" y="40" width="34" height="18" fill="url(#scan-d)" />
        </g>

        {/* envelope body */}
        <rect x="48" y="128" width="290" height="180" rx="16" fill="#f8f8f7" />
        <rect x="48" y="128" width="290" height="180" rx="16" fill="url(#scan-m)" />
        {/* side shading for depth */}
        <rect x="300" y="128" width="38" height="180" fill="url(#scan-d)" opacity="0.55" />
        {/* flap */}
        <path d="M54 136 L193 228 L332 136 Z" fill="#f8f8f7" />
        <path d="M54 136 L193 228 L332 136 Z" fill="url(#scan-l)" />
        {/* lower folds */}
        <path d="M56 300 L150 214 M330 300 L236 214" stroke="#111" strokeWidth="3" strokeDasharray="6 4" />

        {/* face: dark screen with two blinking eyes */}
        <g transform="translate(193 230)">
          <rect x="-58" y="-44" width="116" height="88" rx="18" fill="url(#scan-d)" />
          <rect x="-44" y="-30" width="88" height="60" rx="10" fill="#111" />
          <g className="animate-eyes">
            <rect x="-22" y="-14" width="13" height="26" rx="2" fill="#f8f8f7" />
            <rect x="9" y="-14" width="13" height="26" rx="2" fill="#f8f8f7" />
          </g>
        </g>
      </g>
    </svg>
  );
}
