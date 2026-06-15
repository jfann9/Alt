// Authentic-looking Alt site footer (dark), recreated to match the real
// alt.xyz footer so the concept reads as a genuine product surface.

import AltLogo from './AltLogo.jsx'

const LINKS = [
  'Buy',
  'Sell',
  'Borrow',
  'Vault',
  'Company',
  'Careers',
  'Blog',
  'Help',
  'Terms',
  'Privacy',
]

const SOCIALS = ['TikTok', 'X', 'Instagram', 'Facebook', 'LinkedIn']

// Small dark app-store badge (recreated, no external image needed).
function StoreBadge({ glyph, top, bottom }) {
  return (
    <div className="flex w-44 items-center gap-3 rounded-lg border border-white/25 bg-black px-3 py-2 text-white">
      <span className="text-2xl leading-none">{glyph}</span>
      <span className="leading-tight">
        <span className="block text-[10px] text-white/70">{top}</span>
        <span className="block text-sm font-semibold">{bottom}</span>
      </span>
    </div>
  )
}

export default function Footer() {
  return (
    <footer className="bg-[#0b0b0d] text-white">
      <div className="mx-auto grid max-w-7xl grid-cols-1 gap-10 px-8 py-12 md:grid-cols-3">
        {/* Left: logo + contact */}
        <div>
          <AltLogo className="h-12 invert" />
          <p className="mt-8 text-sm text-white/85">Get started on Alt.</p>
          <p className="mt-6 text-sm text-white/70">Reach out to our collector support team:</p>
          <p className="mt-2 text-sm text-white/70">Email - support@alt.xyz</p>
          <p className="text-sm text-white/70">Text - (833) 483-5949</p>
          <p className="mt-16 text-sm text-white/60">
            Copyright © 2026 ALT.XYZ, All rights reserved.
          </p>
        </div>

        {/* Middle: link list */}
        <nav className="md:px-6">
          {LINKS.map((l) => (
            <a
              key={l}
              href="#"
              onClick={(e) => e.preventDefault()}
              className="block border-b border-white/10 py-2.5 text-sm font-medium text-white/90 hover:text-white"
            >
              {l}
            </a>
          ))}
        </nav>

        {/* Right: app download + socials */}
        <div>
          <h3 className="text-sm font-semibold text-white/85">Download App</h3>
          <div className="mt-4 flex flex-col gap-3">
            <StoreBadge glyph="" top="Available on the" bottom="App Store" />
            <StoreBadge glyph="▶" top="GET IT ON" bottom="Google Play" />
          </div>
          <div className="mt-10 flex items-center gap-4 text-white/80">
            {SOCIALS.map((s) => (
              <span
                key={s}
                title={s}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-white/25 text-[11px] font-bold"
              >
                {s[0]}
              </span>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}
