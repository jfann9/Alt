// A single card in Gallery View: art shown large and prominently, with a light
// "framed" treatment. Value/grade sit beneath so the finance data is still there
// but secondary to the art.

import { usd, pct, gainColor } from '../data/format.js'

export default function CardTile({ card, selectable, selected, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`group flex flex-col overflow-hidden rounded-2xl border bg-white text-left transition-all duration-150 hover:-translate-y-1 hover:shadow-xl ${
        selected ? 'border-alt-purple ring-2 ring-alt-purple' : 'border-alt-line'
      } ${selectable ? 'cursor-pointer' : 'cursor-default'}`}
    >
      {/* Art panel — soft gradient frame echoing Alt's showcase look */}
      <div className="relative flex items-center justify-center bg-gradient-to-b from-gray-50 to-gray-100 p-4">
        <img
          src={card.image}
          alt={card.short}
          className="h-56 w-auto rounded-lg object-contain drop-shadow-md"
        />
        {card.vaulted && (
          <span className="absolute right-3 top-3 rounded-full bg-white/90 px-2 py-0.5 text-[10px] font-bold text-alt-purple shadow">
            ✓ VAULTED
          </span>
        )}
        {selectable && (
          <span
            className={`absolute left-3 top-3 flex h-6 w-6 items-center justify-center rounded-full border text-xs font-bold ${
              selected
                ? 'border-alt-purple bg-alt-purple text-white'
                : 'border-alt-gray bg-white/90 text-alt-gray'
            }`}
          >
            {selected ? '✓' : '+'}
          </span>
        )}
      </div>

      {/* Meta */}
      <div className="flex flex-1 flex-col gap-1 border-t border-alt-line p-3">
        <div className="text-sm font-bold leading-tight">{card.short}</div>
        <div className="text-xs text-alt-gray">{card.grade}</div>
        <div className="mt-1 flex items-center justify-between">
          <span className="text-sm font-extrabold">Ⓐ {usd(card.altValue)}</span>
          <span className={`text-xs font-bold ${gainColor(card.gainLossPct)}`}>
            {pct(card.gainLossPct)}
          </span>
        </div>
      </div>
    </button>
  )
}
