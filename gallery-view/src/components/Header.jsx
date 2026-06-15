// Top navigation bar + sub-nav tabs, styled to match Alt's real "My Collection"
// screen as closely as possible. The TOTAL VALUE pill sits on the tabs row
// (right side) exactly like the real product. The List/Gallery toggle lives in
// the Toolbar (next to Filter By), not here.

import AltLogo from './AltLogo.jsx'
import { usd, pct, gainColor } from '../data/format.js'

export default function Header({ totalValue, allTimePct }) {
  return (
    <header className="border-b border-alt-line bg-white">
      {/* Top row: logo, search, primary nav, SELL, menu */}
      <div className="mx-auto flex max-w-7xl items-center gap-6 px-6 py-3">
        <AltLogo className="h-7 text-alt-ink" />

        <div className="flex flex-1 items-center gap-2 rounded-full border border-alt-line px-4 py-2.5 text-sm text-alt-gray">
          <span>🔍</span>
          <span>Search by name or cert #</span>
        </div>

        <nav className="hidden items-center gap-6 md:flex">
          <span className="text-xs font-bold tracking-wide text-alt-ink">ALL ITEMS</span>
          <span className="flex items-center gap-1.5 text-xs font-bold tracking-wide text-alt-ink">
            AUCTIONS
            <span className="rounded bg-alt-red px-1.5 py-0.5 text-[10px] font-bold text-white">
              LIVE
            </span>
          </span>
          <span className="text-xs font-bold tracking-wide text-alt-ink">MARKET TRENDS</span>
          <span className="text-xs font-bold tracking-wide text-alt-purple">
            MY COLLECTION
          </span>
        </nav>

        <button className="rounded-lg bg-alt-purple px-5 py-2.5 text-sm font-bold text-white hover:bg-alt-purple-dark">
          SELL
        </button>

        <button className="flex flex-col gap-1" aria-label="Menu">
          <span className="block h-0.5 w-6 bg-alt-ink" />
          <span className="block h-0.5 w-6 bg-alt-ink" />
        </button>
      </div>

      {/* Sub-nav row: collection tabs (left, black) + TOTAL VALUE pill (right) */}
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-7 text-lg font-bold">
          <span className="border-b-2 border-alt-purple pb-3 text-alt-purple">
            My collection
          </span>
          <span className="pb-3 text-alt-ink">Fixed price</span>
          <span className="pb-3 text-alt-ink">Auction</span>
          <span className="pb-3 text-alt-ink">Sold</span>
        </div>

        <div className="mb-1 flex items-center gap-3 rounded-lg bg-alt-green-bg px-5 py-2">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-alt-gray">
            Total Value
          </span>
          <span className="text-xl font-extrabold">{usd(totalValue)}</span>
          <span className={`text-sm font-bold ${gainColor(allTimePct)}`}>
            {pct(allTimePct)}
          </span>
          <span className="text-xs text-alt-gray">(all time)</span>
        </div>
      </div>
    </header>
  )
}
