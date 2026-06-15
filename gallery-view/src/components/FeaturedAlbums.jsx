// Community "Explore" section: albums from other (fake) users with static like
// counts. Display only — shows the social/discovery angle. Each cover fans out
// the album's cards.

import { featuredAlbums } from '../data/mockData.js'

const likeLabel = (n) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`)

export default function FeaturedAlbums() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold">Featured Albums</h2>
        <span className="text-sm font-semibold text-alt-purple">Explore all →</span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {featuredAlbums.map((a) => (
          <div
            key={a.id}
            className="overflow-hidden rounded-2xl border border-alt-line bg-white transition-shadow hover:shadow-lg"
          >
            {/* Fanned multi-card cover */}
            <div className="flex h-44 items-center justify-center gap-3 bg-gradient-to-b from-gray-50 to-gray-100 p-4">
              {a.coverImages.map((img, i) => (
                <img
                  key={i}
                  src={img}
                  alt=""
                  className="h-full w-auto rounded-lg object-contain drop-shadow-md"
                />
              ))}
            </div>
            <div className="flex items-center justify-between p-4">
              <div>
                <div className="text-base font-bold leading-tight">{a.title}</div>
                <div className="text-xs text-alt-gray">
                  {a.subtitle} · {a.user}
                </div>
              </div>
              <div className="flex items-center gap-1 text-sm font-semibold text-alt-gray">
                <span className="text-alt-red">♥</span> {likeLabel(a.likes)}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
