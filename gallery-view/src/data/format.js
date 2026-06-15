// Small display helpers shared across components.

// "$4,250" — whole-dollar currency, Alt-style.
export const usd = (n) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

// "+15.95%" / "-7.14%" with a sign, for gain/loss cells.
export const pct = (n) => `${n >= 0 ? '▲' : '▼'} ${Math.abs(n).toFixed(2)}%`

// Tailwind text color class for a gain/loss value.
export const gainColor = (n) => (n >= 0 ? 'text-alt-green' : 'text-alt-red')
