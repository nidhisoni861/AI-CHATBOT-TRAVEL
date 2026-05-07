export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#eef3fb] px-6 text-center text-slate-950">
      <div className="rounded-3xl border border-white/70 bg-white p-8 shadow-[0_18px_45px_rgba(15,23,42,.1)]">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">404</p>
        <h1 className="mt-2 text-2xl font-bold">Page not found</h1>
        <p className="mt-2 text-sm text-slate-600">Return to the travel assistant dashboard from the home page.</p>
      </div>
    </main>
  );
}
