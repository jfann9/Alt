// Showcase Mode overlay: a full-bleed presentation of an album against a
// pre-rendered AI background (faked "generation" — instant swap). Demonstrates
// the concept of an art-complementing themed backdrop for an album.

export default function ShowcaseMode({ album, cards, onClose }) {
  // Feature a curated subset (e.g. the water evolution line) if specified,
  // otherwise the whole album.
  const featuredIds = album.showcaseCardIds ?? album.cardIds
  const albumCards = featuredIds
    .map((id) => cards.find((c) => c.id === id))
    .filter(Boolean)

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/80">
      {/* Background image fills the screen */}
      <img
        src={album.showcase}
        alt="Showcase background"
        className="absolute inset-0 h-full w-full object-cover"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-black/40" />

      {/* Top bar */}
      <div className="relative z-10 flex items-center justify-between px-8 py-5">
        <div className="text-white">
          <div className="text-xs font-semibold uppercase tracking-widest text-white/70">
            Showcase Mode · AI Background
          </div>
          <div className="text-2xl font-extrabold drop-shadow">{album.name}</div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg bg-white/90 px-4 py-2 text-sm font-bold text-alt-ink hover:bg-white"
        >
          Exit Showcase
        </button>
      </div>

      {/* Floating cards */}
      <div className="relative z-10 flex flex-1 flex-wrap items-center justify-center gap-6 px-8 pb-12">
        {albumCards.map((c) => (
          <img
            key={c.id}
            src={c.image}
            alt={c.short}
            className="h-72 w-auto rounded-xl shadow-2xl ring-1 ring-white/30 transition-transform duration-200 hover:-translate-y-2 sm:h-80"
          />
        ))}
      </div>

      <div className="relative z-10 px-8 pb-6 text-center text-xs text-white/70">
        Background pre-rendered for this demo — in production, generated to match the
        album's dominant colors and themes.
      </div>
    </div>
  )
}
