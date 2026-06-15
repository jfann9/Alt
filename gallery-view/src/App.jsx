// Top-level app: owns all state for the concept (current view, selected album,
// the album list, modal + showcase visibility) and composes the page.

import { useMemo, useState } from 'react'
import Header from './components/Header.jsx'
import Toolbar from './components/Toolbar.jsx'
import AlbumStrip from './components/AlbumStrip.jsx'
import ListView from './components/ListView.jsx'
import GalleryView from './components/GalleryView.jsx'
import CreateAlbumModal from './components/CreateAlbumModal.jsx'
import FeaturedAlbums from './components/FeaturedAlbums.jsx'
import BusinessCallout from './components/BusinessCallout.jsx'
import Footer from './components/Footer.jsx'
import { cards, seedAlbums } from './data/mockData.js'

export default function App() {
  const [view, setView] = useState('list') // 'list' | 'gallery' — open on List (Alt's default)
  const [albums, setAlbums] = useState(seedAlbums)
  const [activeAlbumId, setActiveAlbumId] = useState('all')
  const [albumView, setAlbumView] = useState('standard') // 'standard' | 'art'
  const [showCreate, setShowCreate] = useState(false)

  const activeAlbum = albums.find((a) => a.id === activeAlbumId) || null

  // Selecting an album always starts on the standard grid.
  const selectAlbum = (id) => {
    setActiveAlbumId(id)
    setAlbumView('standard')
  }

  // List View always shows the full collection (so it mirrors Alt exactly).
  // Album filtering only applies in Gallery View, where albums live.
  const visibleCards = useMemo(() => {
    if (view === 'list' || !activeAlbum) return cards
    return cards.filter((c) => activeAlbum.cardIds.includes(c.id))
  }, [view, activeAlbum])

  // Total value + all-time gain for the header pill, derived from what's shown.
  const { totalValue, allTimePct } = useMemo(() => {
    const value = visibleCards.reduce((s, c) => s + c.altValue, 0)
    const cost = visibleCards.reduce((s, c) => s + c.costBasis, 0)
    return { totalValue: value, allTimePct: cost > 0 ? ((value - cost) / cost) * 100 : 0 }
  }, [visibleCards])

  // Save a new in-memory album from the modal, then jump to it.
  const handleCreateAlbum = (name, cardIds) => {
    const id = `album-${name.toLowerCase().replace(/\s+/g, '-')}-${albums.length}`
    setAlbums((prev) => [...prev, { id, name, emoji: '🗂️', cardIds, showcase: null }])
    setShowCreate(false)
    setActiveAlbumId(id)
  }

  return (
    <div className="min-h-full bg-white">
      <Header totalValue={totalValue} allTimePct={allTimePct} />

      <Toolbar count={visibleCards.length} view={view} setView={setView} />

      {view === 'list' ? (
        <ListView cards={visibleCards} />
      ) : (
        <>
          <AlbumStrip
            albums={albums}
            activeId={activeAlbumId}
            onSelect={selectAlbum}
            onCreate={() => setShowCreate(true)}
            cards={cards}
          />
          <GalleryView
            cards={visibleCards}
            activeAlbum={activeAlbum}
            albumView={albumView}
            setAlbumView={setAlbumView}
          />
        </>
      )}

      <FeaturedAlbums />
      <BusinessCallout />
      <Footer />

      {showCreate && (
        <CreateAlbumModal
          cards={cards}
          onClose={() => setShowCreate(false)}
          onSave={handleCreateAlbum}
        />
      )}
    </div>
  )
}
