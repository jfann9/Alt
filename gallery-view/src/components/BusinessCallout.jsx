// Footer callout framing the business rationale for the Gallery View concept.

export default function BusinessCallout() {
  return (
    <footer className="border-t border-alt-line bg-alt-purple-light/40">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <div className="rounded-2xl border border-alt-line bg-white p-5">
          <div className="mb-1 text-xs font-bold uppercase tracking-widest text-alt-purple">
            Concept rationale
          </div>
          <p className="text-sm leading-relaxed text-alt-ink">
            Gallery and album features reframe a collection around the{' '}
            <span className="font-semibold">art and emotional value</span> of cards — not
            just valuation. This increases session time and emotional attachment to
            collections, which correlates with higher marketplace engagement and listing
            rates.
          </p>
        </div>
        <div className="mt-4 text-center text-xs text-alt-gray">
          Concept demo · static mockup · not an official Alt product
        </div>
      </div>
    </footer>
  )
}
