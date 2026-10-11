export default function LoginPage() {
  return (
    <section className="mx-auto max-w-xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-[0.16em] text-emerald-600">Authentication</p>
      <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">Login</h1>
      <p className="mt-2 text-slate-600">Placeholder login screen for PawCare.</p>
      <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-600">
        Login form, password reset flow, and auth state handling are intentionally deferred to the backend auth task.
      </div>
    </section>
  );
}
