export default function Home() {
  return (
    <section className="space-y-8">
      <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-emerald-600">PawCare</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Pet health support for everyday care.
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-600">
          Keep pet profiles, track health records, assess symptoms, and review preventive care guidance in one place.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[
          { title: "Profile", text: "Manage pet details, age, and care history." },
          { title: "Assessment", text: "Capture symptom context and review urgency guidance." },
          { title: "Assistant", text: "Ask health questions grounded in trusted sources." },
        ].map((card) => (
          <div key={card.title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold text-slate-900">{card.title}</h2>
            <p className="mt-3 text-slate-600">{card.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
