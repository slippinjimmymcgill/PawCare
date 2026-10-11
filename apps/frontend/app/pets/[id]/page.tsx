export default function PetDetailPage({ params }: { params: { id: string } }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-amber-600">Pet profile</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">Pet #{params.id}</h1>
      <p className="mt-2 text-slate-600">This placeholder page will include the pet overview, details, and health summary.</p>
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="text-sm text-slate-500">Records</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">0</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="text-sm text-slate-500">Vaccinations</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">0</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="text-sm text-slate-500">Reminders</div>
          <div className="mt-2 text-xl font-semibold text-slate-900">0</div>
        </div>
      </div>
    </section>
  );
}
