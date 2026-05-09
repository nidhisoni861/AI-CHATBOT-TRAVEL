import { Bookmark } from "lucide-react";

const trips = [
  {
    title: "Santorini Escape",
    date: "May 20 – May 27, 2025",
    from: "Athens",
    to: "Santorini",
    days: "8 Days",
    badge: "SE",
    icon: "⛪",
    border: "border-purple-200",
    bg: "bg-purple-50/45",
    badgeBg: "bg-purple-600",
    text: "text-purple-600",
    pill: "bg-purple-100 text-purple-700",
  },
  {
    title: "Japan Discovery",
    date: "Apr 12 – Apr 20, 2025",
    from: "Tokyo",
    to: "Kyoto",
    days: "9 Days",
    badge: "JD",
    icon: "🏯",
    border: "border-rose-200",
    bg: "bg-rose-50/45",
    badgeBg: "bg-rose-500",
    text: "text-rose-500",
    pill: "bg-rose-100 text-rose-700",
  },
  {
    title: "Maldives Retreat",
    date: "Jul 5 – Jul 12, 2025",
    from: "Malé",
    to: "Baa Atoll",
    days: "7 Days",
    badge: "MR",
    icon: "🌴",
    border: "border-teal-200",
    bg: "bg-teal-50/45",
    badgeBg: "bg-teal-600",
    text: "text-teal-600",
    pill: "bg-teal-100 text-teal-700",
  },
];

export default function SavedTripsPanel() {
  return (
    <aside className="w-full rounded-[28px] border border-white/70 bg-white/80 p-4 shadow-[0_24px_70px_rgba(15,23,42,0.20)] backdrop-blur-2xl">
      <header className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Bookmark className="h-5 w-5 text-slate-800" />
          <h2 className="text-base font-extrabold tracking-tight text-slate-950 2xl:text-lg">
            Saved Trips
          </h2>
        </div>

        <button className="text-sm font-extrabold text-teal-700 transition hover:text-teal-900">
          View all
        </button>
      </header>

      <div className="space-y-3">
        {trips.map((trip) => (
          <article
            key={trip.title}
            className={`relative overflow-hidden rounded-[22px] border ${trip.border} ${trip.bg} p-4 shadow-[0_12px_34px_rgba(15,23,42,0.08)]`}
          >
            <div
              className={`absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-full ${trip.badgeBg} text-xs font-extrabold text-white shadow-lg`}
            >
              {trip.badge}
            </div>

            <div className="flex gap-3">
              <div
                className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white/70 text-4xl ${trip.text}`}
              >
                <span>{trip.icon}</span>
              </div>

              <div className="min-w-0 pr-9">
                <h3 className="truncate text-base font-extrabold text-slate-950">
                  {trip.title}
                </h3>
                <p className="mt-1 text-xs font-bold leading-snug text-slate-500">
                  {trip.date}
                </p>
              </div>
            </div>

            <div className="mt-4 flex items-center gap-2.5">
              <span className="text-xs font-extrabold text-slate-800 2xl:text-sm">
                {trip.from}
              </span>

              <div className="flex flex-1 items-center justify-center gap-1.5">
                <span className={`h-1.5 w-1.5 rounded-full ${trip.badgeBg}`} />
                <span className={`h-px flex-1 ${trip.badgeBg} opacity-30`} />
                <span className={`h-1.5 w-1.5 rounded-full ${trip.badgeBg}`} />
                <span className={`h-px flex-1 ${trip.badgeBg} opacity-30`} />
                <span className={`h-1.5 w-1.5 rounded-full ${trip.badgeBg}`} />
              </div>

              <span className="text-xs font-extrabold text-slate-800 2xl:text-sm">
                {trip.to}
              </span>
            </div>

            <div className="mt-3 flex justify-center">
              <span
                className={`rounded-full px-4 py-2 text-xs font-extrabold ${trip.pill}`}
              >
                {trip.days}
              </span>
            </div>
          </article>
        ))}
      </div>
    </aside>
  );
}