export default function RegisterPage() {
  return (
    <section className="mx-auto max-w-xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-violet-600">New account</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">Register</h1>
      <p className="mt-2 text-slate-600">This screen is a placeholder for the owner registration flow.</p>
      <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
        Registration form and validation will be implemented after the backend auth endpoints are available.
      </div>
    </section>
  );
}
