// The row directly above the collection, matching Alt: item count + a search box
// on the left, controls on the right. The List/Gallery toggle sits next to the
// Filter By dropdown (per design request) so there's no wasted vertical space.

function ViewToggle({ view, setView }) {
  const base = 'px-3.5 py-1.5 text-sm font-semibold rounded-md transition-colors duration-150'
  return (
    <div className="inline-flex items-center gap-1 rounded-lg bg-alt-purple-light p-1">
      <button
        className={`${base} ${
          view === 'list' ? 'bg-white text-alt-purple shadow-sm' : 'text-alt-gray'
        }`}
        onClick={() => setView('list')}
      >
        List View
      </button>
      <button
        className={`${base} ${
          view === 'gallery' ? 'bg-white text-alt-purple shadow-sm' : 'text-alt-gray'
        }`}
        onClick={() => setView('gallery')}
      >
        Gallery View
      </button>
    </div>
  )
}

export default function Toolbar({ count, view, setView }) {
  return (
    <div className="mx-auto max-w-7xl px-6">
      <div className="flex items-center justify-between gap-4 py-3">
        {/* Left: item count + search (matches Alt) */}
        <div className="flex items-center gap-5">
          <span className="text-sm font-semibold text-alt-gray">
            {count} {count === 1 ? 'ITEM' : 'ITEMS'}
          </span>
          <div className="flex items-center gap-2 text-sm text-alt-gray">
            <span>🔍</span>
            <span>Search</span>
          </div>
        </div>

        {/* Right: view toggle + Filter By */}
        <div className="flex items-center gap-3">
          <ViewToggle view={view} setView={setView} />
          <button className="flex items-center gap-2 rounded-lg border border-alt-line px-4 py-1.5 text-sm font-semibold text-alt-ink">
            Filter By <span className="text-alt-gray">▾</span>
          </button>
        </div>
      </div>
    </div>
  )
}
