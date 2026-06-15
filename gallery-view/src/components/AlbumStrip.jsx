// Horizontal strip of the collector's albums. Acts as a filter: clicking an
// album narrows both List and Gallery views to that album's cards. "All" resets,
// and "+ Create Album" opens the create-album modal.

export default function AlbumStrip({ albums, activeId, onSelect, onCreate, cards }) {
  const chip =
    'flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition-colors'

  // Tiny cover preview = first card image in the album.
  const coverFor = (album) => {
    const first = cards.find((c) => album.cardIds.includes(c.id))
    return first?.image
  }

  return (
    <div className="mx-auto max-w-7xl px-6 pt-5">
      <div className="mb-2 text-sm font-bold text-alt-ink">Albums</div>
      <div className="flex items-center gap-3 overflow-x-auto pb-2">
        <button
          className={`${chip} ${
            activeId === 'all'
              ? 'border-alt-purple bg-alt-purple text-white'
              : 'border-alt-line bg-white text-alt-ink hover:border-alt-purple'
          }`}
          onClick={() => onSelect('all')}
        >
          All items
        </button>

        {albums.map((a) => (
          <button
            key={a.id}
            className={`${chip} ${
              activeId === a.id
                ? 'border-alt-purple bg-alt-purple text-white'
                : 'border-alt-line bg-white text-alt-ink hover:border-alt-purple'
            }`}
            onClick={() => onSelect(a.id)}
          >
            {coverFor(a) ? (
              <img
                src={coverFor(a)}
                alt=""
                className="h-6 w-5 rounded object-cover"
              />
            ) : (
              <span>{a.emoji ?? '🗂️'}</span>
            )}
            {a.name}
            <span
              className={`rounded-full px-1.5 text-xs ${
                activeId === a.id ? 'bg-white/20' : 'bg-gray-100 text-alt-gray'
              }`}
            >
              {a.cardIds.length}
            </span>
          </button>
        ))}

        <button
          className="flex shrink-0 items-center gap-1 rounded-full border border-dashed border-alt-purple px-4 py-2 text-sm font-semibold text-alt-purple hover:bg-alt-purple-light"
          onClick={onCreate}
        >
          + Create Album
        </button>
      </div>
    </div>
  )
}
