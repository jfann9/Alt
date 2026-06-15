// "Album Art" view of an album: the AI-generated background with the album's
// cards floating on top. This is the presentation the community sees when
// exploring someone's collection. Rendered inline (not a modal) so it toggles
// in place against the standard grid.

export default function AlbumArt({ album, cards }) {
  // Feature a curated subset if specified, otherwise the whole album.
  const featuredIds = album.showcaseCardIds ?? album.cardIds
  const albumCards = featuredIds
    .map((id) => cards.find((c) => c.id === id))
    .filter(Boolean)

  const hasArt = Boolean(album.albumArt)

  return (
    <div className="relative overflow-hidden rounded-3xl shadow-lg">
      {/* Background: AI art if available, otherwise a themed gradient fallback */}
      {hasArt ? (
        <img
          src={album.albumArt}
          alt={`${album.name} background`}
          className="absolute inset-0 h-full w-full object-cover"
        />
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-alt-purple-dark via-indigo-900 to-slate-900" />
      )}
      {/* Legibility overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/15 to-black/35" />

      {/* Caption (top) */}
      <div className="relative z-10 flex items-start justify-between p-6">
        <div className="text-white drop-shadow">
          <div className="text-[11px] font-semibold uppercase tracking-widest text-white/75">
            Album Art · Community view
          </div>
          <div className="text-2xl font-extrabold">{album.name}</div>
        </div>
        {!hasArt && (
          <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold text-white">
            ✨ Generate background
          </span>
        )}
      </div>

      {/* Floating cards */}
      <div className="relative z-10 flex flex-wrap items-center justify-center gap-6 px-6 pb-10 pt-4">
        {albumCards.map((c) => (
          <img
            key={c.id}
            src={c.image}
            alt={c.short}
            className="h-60 w-auto rounded-xl shadow-2xl ring-1 ring-white/30 transition-transform duration-200 hover:-translate-y-2 sm:h-72"
          />
        ))}
      </div>

      {/* Caption (bottom) */}
      <div className="relative z-10 px-6 pb-5 text-center text-xs text-white/75">
        This is what the community sees when exploring this collection.
      </div>
    </div>
  )
}
