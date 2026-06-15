// Finance-forward table that recreates Alt's existing "My Collection" view:
// ITEM | ALT VALUE | COST BASIS | GAIN/LOSS % | LAST COMP | STATUS | VAULTED DATE.

import { usd, pct, gainColor } from '../data/format.js'

function HeadCell({ children, className = '' }) {
  return (
    <th
      className={`px-4 py-3 text-left text-[11px] font-bold uppercase tracking-wide text-alt-gray ${className}`}
    >
      {children}
    </th>
  )
}

export default function ListView({ cards }) {
  return (
    <div className="mx-auto max-w-7xl px-6 pb-4 pt-1 alt-fade">
      <div className="overflow-hidden rounded-xl border border-alt-line">
        <table className="w-full border-collapse">
          <thead className="bg-gray-50">
            <tr>
              <HeadCell>Item</HeadCell>
              <HeadCell>Alt Value</HeadCell>
              <HeadCell>Cost Basis</HeadCell>
              <HeadCell>Gain/Loss %</HeadCell>
              <HeadCell>Last Comp</HeadCell>
              <HeadCell>Status</HeadCell>
              <HeadCell>Vaulted Date</HeadCell>
            </tr>
          </thead>
          <tbody>
            {cards.map((c) => (
              <tr key={c.id} className="border-t border-alt-line hover:bg-gray-50/70">
                {/* Item: thumbnail + title */}
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <img
                      src={c.image}
                      alt={c.short}
                      className="h-14 w-10 rounded object-cover shadow-sm"
                    />
                    <span className="max-w-xs text-sm font-medium leading-snug">
                      {c.name}
                    </span>
                  </div>
                </td>

                {/* Alt Value + range */}
                <td className="px-4 py-3">
                  <div className="text-sm font-bold">Ⓐ {usd(c.altValue)}</div>
                  <div className="text-xs text-alt-gray">
                    {usd(c.valueLow)}–{usd(c.valueHigh)}
                  </div>
                </td>

                <td className="px-4 py-3 text-sm">{usd(c.costBasis)}</td>

                <td className={`px-4 py-3 text-sm font-bold ${gainColor(c.gainLossPct)}`}>
                  {pct(c.gainLossPct)}
                </td>

                <td className="px-4 py-3">
                  <div className="text-sm">{usd(c.lastComp)}</div>
                  <div className="text-xs text-alt-gray">{c.lastCompDate}</div>
                </td>

                <td className="px-4 py-3">
                  {c.vaulted ? (
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-alt-ink">✓ Vaulted</span>
                      <span className="rounded bg-alt-purple px-2 py-0.5 text-[11px] font-bold text-white">
                        SELL
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-alt-gray">Not vaulted</span>
                  )}
                </td>

                <td className="px-4 py-3 text-sm text-alt-gray">{c.vaultedDate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
