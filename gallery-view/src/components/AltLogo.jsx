// Alt wordmark — the official logo image. On dark backgrounds pass
// `invert` in className (the logo's white background flips to black and the
// black wordmark flips to white).

export default function AltLogo({ className = 'h-7' }) {
  return <img src="/alt_logo.png" alt="ALT" className={`w-auto ${className}`} />
}
