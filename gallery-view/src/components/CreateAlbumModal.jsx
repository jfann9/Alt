// Interactive "Create Album" flow. Doesn't persist — it builds an album in
// memory: name it, click cards to add them, then save. The new album shows up in
// the AlbumStrip immediately.

import { useState } from 'react'

export default function CreateAlbumModal({ cards, onClose, onSave }) {
  const [name, setName] = useState('')
  const [picked, setPicked] = useState(() => new Set())

  const toggle = (id) => {
    setPicked((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const canSave = name.trim().length > 0 && picked.size > 0

  return (
    // Backdrop — click outside to close.
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-alt-line px-6 py-4">
          <h2 className="text-lg font-bold">Create Album</h2>
          <button
            className="text-2xl leading-none text-alt-gray hover:text-alt-ink"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <label className="mb-1 block text-sm font-semibold">Album name</label>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder='e.g. "Water-type favorites"'
            className="mb-5 w-full rounded-lg border border-alt-line px-3 py-2 text-sm outline-none focus:border-alt-purple"
          />

          <div className="mb-2 text-sm font-semibold">
            Add cards{' '}
            <span className="font-normal text-alt-gray">({picked.size} selected)</span>
          </div>
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
            {cards.map((c) => {
              const on = picked.has(c.id)
              return (
                <button
                  key={c.id}
                  onClick={() => toggle(c.id)}
                  className={`relative overflow-hidden rounded-lg border p-2 transition-all ${
                    on
                      ? 'border-alt-purple ring-2 ring-alt-purple'
                      : 'border-alt-line hover:border-alt-purple'
                  }`}
                >
                  <img
                    src={c.image}
                    alt={c.short}
                    className="mx-auto h-24 w-auto object-contain"
                  />
                  <div className="mt-1 truncate text-[11px] font-medium">{c.short}</div>
                  <span
                    className={`absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full text-xs font-bold ${
                      on ? 'bg-alt-purple text-white' : 'bg-white/90 text-alt-gray'
                    }`}
                  >
                    {on ? '✓' : '+'}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 border-t border-alt-line px-6 py-4">
          <button
            className="rounded-lg px-4 py-2 text-sm font-semibold text-alt-gray hover:text-alt-ink"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            disabled={!canSave}
            onClick={() => onSave(name.trim(), [...picked])}
            className="rounded-lg bg-alt-purple px-5 py-2 text-sm font-bold text-white enabled:hover:bg-alt-purple-dark disabled:cursor-not-allowed disabled:opacity-40"
          >
            Create Album
          </button>
        </div>
      </div>
    </div>
  )
}
