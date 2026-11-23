/**
 * Amtspost's mascot: a friendly letter with a gradient "screen" seal,
 * floating above a dark plinth.
 */
export default function MailBot({ className = "" }: { className?: string }) {
  return (
    <div className={`relative flex flex-col items-center ${className}`} aria-hidden>
      <svg viewBox="0 0 320 300" className="animate-float w-full max-w-[340px] drop-shadow-[0_30px_30px_rgba(0,0,0,0.18)]">
        <defs>
          <linearGradient id="mb-accent" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#f2703a" />
            <stop offset="1" stopColor="#ff4f9a" />
          </linearGradient>
          <linearGradient id="mb-paper" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#ffffff" />
            <stop offset="1" stopColor="#e9e6df" />
          </linearGradient>
          <linearGradient id="mb-side" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#d9d5cc" />
            <stop offset="1" stopColor="#f4f2ed" />
          </linearGradient>
        </defs>

        {/* document sticking out of the envelope */}
        <g transform="rotate(-6 160 80)">
          <rect x="92" y="18" width="136" height="120" rx="6" fill="#fbfaf7" stroke="#16161622" />
          <rect x="108" y="38" width="62" height="6" rx="3" fill="#16161633" />
          <rect x="108" y="54" width="96" height="5" rx="2.5" fill="#16161620" />
          <rect x="108" y="66" width="84" height="5" rx="2.5" fill="#16161620" />
          <rect x="108" y="78" width="90" height="5" rx="2.5" fill="#16161620" />
          <rect x="178" y="34" width="34" height="14" rx="3" fill="url(#mb-accent)" opacity="0.9" />
        </g>

        {/* envelope body with a little depth */}
        <path d="M44 112 L276 112 L284 120 L284 262 L52 262 L44 254 Z" fill="url(#mb-side)" />
        <rect x="36" y="104" width="240" height="150" rx="14" fill="url(#mb-paper)" stroke="#16161626" />
        <path d="M36 118 L156 196 L276 118" fill="none" stroke="#16161624" strokeWidth="2" />
        <path d="M36 246 L120 176 M276 246 L192 176" stroke="#1616161a" strokeWidth="2" />

        {/* gradient seal = face */}
        <g transform="translate(156 186)">
          <rect x="-50" y="-40" width="100" height="80" rx="20" fill="url(#mb-accent)" />
          <rect x="-38" y="-28" width="76" height="56" rx="12" fill="#161616" />
          <g className="animate-eyes">
            <rect x="-20" y="-12" width="12" height="22" rx="6" fill="#f5f3ee" />
            <rect x="8" y="-12" width="12" height="22" rx="6" fill="#f5f3ee" />
          </g>
        </g>
        {/* tiny status light */}
        <circle cx="258" cy="124" r="4" fill="#3ddc84" />
      </svg>

      {/* plinth */}
      <div className="relative -mt-2 h-36 w-56 sm:w-64">
        <div className="absolute inset-x-0 top-0 h-6 -skew-x-[30deg] bg-[#2b2b2b]" />
        <div className="absolute inset-x-0 bottom-0 top-3 bg-gradient-to-b from-[#232323] to-[#111]" />
      </div>
    </div>
  );
}
