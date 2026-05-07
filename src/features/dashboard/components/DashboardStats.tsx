import { Clock, Globe2, Languages, MapPin, MessageSquare, TrendingUp } from "lucide-react";

export function DashboardStats() {
  const stats = [
    { label: "Trips Planned", value: "12", change: "+3 this week", icon: MapPin, accent: "blue" },
    { label: "Conversations", value: "47", change: "8 active today", icon: MessageSquare, accent: "emerald" },
    { label: "Hours Saved", value: "38h", change: "AI optimized", icon: Clock, accent: "violet" },
    { label: "Countries Explored", value: "8", change: "+2 planned", icon: Globe2, accent: "orange" },
    { label: "User Preferences", value: "English, EUR", change: "Cultural explorer, mid-range", icon: Languages, accent: "slate" },
  ];

  const accents: Record<string, string> = {
    blue: "from-blue-500 to-indigo-500 bg-blue-50 text-blue-700 border-blue-100",
    emerald: "from-emerald-500 to-teal-500 bg-emerald-50 text-emerald-700 border-emerald-100",
    violet: "from-violet-500 to-fuchsia-500 bg-violet-50 text-violet-700 border-violet-100",
    orange: "from-orange-500 to-amber-500 bg-orange-50 text-orange-700 border-orange-100",
    slate: "from-slate-700 to-blue-700 bg-slate-50 text-slate-700 border-slate-200",
  };

  return (
    <div className="grid grid-cols-5 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        const [gradient, chip] = accents[stat.accent].split(" bg-");
        return (
          <div
            key={stat.label}
            className="group relative overflow-hidden rounded-2xl border border-white/70 bg-white/85 p-4 shadow-[0_18px_45px_rgba(15,23,42,.08)] backdrop-blur transition hover:-translate-y-0.5 hover:shadow-[0_24px_60px_rgba(15,23,42,.12)]"
          >
            <div className="absolute right-0 top-0 h-24 w-24 translate-x-8 -translate-y-8 rounded-full bg-blue-100/60 blur-2xl" />
            <div className="relative flex items-start justify-between gap-3">
              <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white shadow-lg`}>
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Live
              </div>
            </div>
            <div className="relative mt-4">
              <div className="text-2xl font-bold tracking-tight text-slate-950">{stat.value}</div>
              <div className="mt-1 text-sm font-medium text-slate-600">{stat.label}</div>
              <div className={`mt-3 inline-flex rounded-full border bg-${chip} px-2.5 py-1 text-xs font-semibold`}>
                <TrendingUp className="mr-1 h-3.5 w-3.5" />
                {stat.change}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
