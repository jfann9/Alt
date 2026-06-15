// Gallery View: the art-forward reframing of the collection. Shows a responsive
// grid of large card images. When a specific album is open, a second toggle
// appears — "Standard" (the grid) vs "Album Art" (AI background + floating
// cards, i.e. the community-facing presentation).

import CardTile from './CardTile.jsx'
import AlbumArt from './AlbumArt.jsx'

function AlbumViewToggle({ albumView, setAlbumView }) {
  const base = 'px-3.5 py-1.5 text-sm font-semibold rounded-md transition-colors duration-150'
  return (
    <div className="inline-flex items-center gap-1 rounded-lg bg-alt-purple-light p-1">
      <button
        className={`${base} ${
          albumView === 'standard' ? 'bg-white text-alt-purple shadow-sm' : 'text-alt-gray'
        }`}
        onClick={() => setAlbumView('standard')}
      >
        Standard
      </button>
      <button
        className={`${base} ${
          albumView === 'art' ? 'bg-white text-alt-purple shadow-sm' : 'text-alt-gray'
        }`}
        onClick={() => setAlbumView('art')}
      >
        Album Art
      </button>
    </div>
  )
}

export default function GalleryView({ cards, activeAlbum, albumView, setAlbumView }) {
  const Grid = (
    <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
      {cards.map((c) => (
        <CardTile key={c.id} card={c} />
      ))}
    </div>
  )

  return (
    <div className="mx-auto max-w-7xl px-6 pb-6 pt-2 alt-fade">
      {/* Inside a specific album: show its name + the Standard/Album Art toggle */}
      {activeAlbum && (
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-xl font-bold">{activeAlbum.name}</h2>
          <AlbumViewToggle albumView={albumView} setAlbumView={setAlbumView} />
        </div>
      )}

      {cards.length === 0 ? (
        <div className="py-16 text-center text-alt-gray">No cards in this album yet.</div>
      ) : activeAlbum && albumView === 'art' ? (
        <AlbumArt album={activeAlbum} cards={cards} />
      ) : (
        Grid
      )}
    </div>
  )
}
