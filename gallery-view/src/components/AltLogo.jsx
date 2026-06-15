// Alt wordmark, hand-built to match the real logo: a crossbar-less "Λ" peak
// followed by L and T, heavy geometric strokes, black.

export default function AltLogo({ className = 'h-7' }) {
  return (
    <svg
      viewBox="0 0 132 40"
      className={className}
      role="img"
      aria-label="ALT"
      fill="none"
      stroke="currentColor"
      strokeWidth="7"
      strokeLinecap="butt"
      strokeLinejoin="miter"
    >
      {/* Λ — A without a crossbar */}
      <polyline points="4,36 21,5 38,36" />
      {/* L */}
      <polyline points="52,5 52,36 70,36" />
      {/* T */}
      <line x1="80" y1="8" x2="124" y2="8" />
      <line x1="102" y1="8" x2="102" y2="36" />
    </svg>
  )
}
