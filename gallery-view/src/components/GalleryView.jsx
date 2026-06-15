// Gallery View: the art-forward reframing of the collection. Replaces the table
// with a responsive grid of large card images. When an album with a showcase
// background is active, a "Showcase Mode" banner is offered above the grid.

import CardTile from './CardTile.jsx'

export default function GalleryView({ cards, showcaseAvailable, onShowcase }) {
  return (
    <div className="mx-auto max-w-7xl px-6 py-6 alt-fade">
      {showcaseAvailable && (
        <div className="mb-6 flex items-center justify-between rounded-2xl bg-gradient-to-r from-alt-purple-light to-white p-4">
          <div>
            <div className="text-sm font-bold text-alt-ink">✨ Showcase Mode available</div>
            <div className="text-xs text-alt-gray">
              Generate an AI background that complements this album's art.
            </div>
          </div>
          <button
            onClick={onShowcase}
            className="rounded-lg bg-alt-purple px-4 py-2 text-sm font-bold text-white hover:bg-alt-purple-dark"
          >
            Generate Background
          </button>
        </div>
      )}

      {cards.length === 0 ? (
        <div className="py-16 text-center text-alt-gray">No cards in this album yet.</div>
      ) : (
        <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 lg:grid-cols-4">
          {cards.map((c) => (
            <CardTile key={c.id} card={c} />
          ))}
        </div>
      )}
    </div>
  )
}
