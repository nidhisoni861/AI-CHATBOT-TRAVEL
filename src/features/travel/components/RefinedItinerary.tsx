import { useState } from "react";
import { Bookmark, CalendarDays, CloudSun, Languages, MapPinned, RefreshCw, Train, Wallet } from "lucide-react";
import type { ItineraryStop } from "@/lib/api";

function placeImageUrl(name: string) {
  const seed = encodeURIComponent(name.toLowerCase().replace(/\s+/g, "-"));
  return `https://picsum.photos/seed/${seed}/160/128`;
}

const TINTS = ["from-blue-500 to-sky-400", "from-violet-500 to-fuchsia-400", "from-emerald-500 to-teal-400", "from-orange-500 to-amber-400", "from-rose-500 to-pink-400", "from-cyan-500 to-blue-400", "from-amber-500 to-orange-400"];

const STATIC_STOPS = [
  { id: 1, name: "Eiffel Tower", tag: "Landmark", time: "09:00", duration: "2h", cost: "EUR 25", distance: "4.2 km", transport: "Metro", tint: TINTS[0] },
  { id: 2, name: "Louvre Museum", tag: "Museum", time: "12:00", duration: "3h", cost: "EUR 17", distance: "1.8 km", transport: "Walk", tint: TINTS[1] },
  { id: 3, name: "Seine River Cruise", tag: "Experience", time: "16:00", duration: "1h", cost: "EUR 18", distance: "1.2 km", transport: "Walk", tint: TINTS[2] },
  { id: 4, name: "Montmartre", tag: "Neighborhood", time: "18:30", duration: "1.5h", cost: "Free", distance: "5.3 km", transport: "Metro", tint: TINTS[3] },
];

function liveToDisplay(liveStops: ItineraryStop[]) {
  return liveStops.map((s, i) => ({
    id: i + 1,
    name: s.name,
    tag: s.type.replace(/_/g, " "),
    time: `Day ${s.day}`,
    duration: `${s.duration_minutes}min`,
    cost: s.estimated_cost > 0 ? `${s.currency} ${s.estimated_cost}` : "Free",
    distance: "",
    transport: "",
    tint: TINTS[i % TINTS.length],
  }));
}

interface RefinedItineraryProps {
  activeStopId: number;
  onStopChange: (stopId: number) => void;
  liveStops?: ItineraryStop[];
  tripSummary?: Record<string, unknown>;
}

export function RefinedItinerary({ activeStopId, onStopChange, liveStops, tripSummary }: RefinedItineraryProps) {
  const [status, setStatus] = useState("Itinerary updated");
  const hasLive = Array.isArray(liveStops) && liveStops.length > 0;
  const stops = hasLive ? liveToDisplay(liveStops!) : STATIC_STOPS;
  const activeStop = stops.find((stop) => stop.id === activeStopId) ?? stops[0];

  const actions = [
    { icon: MapPinned, label: "Map focused" },
    { icon: Languages, label: "Translation queued" },
    { icon: Bookmark, label: "Stop saved" },
    { icon: RefreshCw, label: "Replacement requested" },
  ];

  const weather = tripSummary as Record<string, unknown> | undefined;
  const weatherStr = (weather?.weather as string) || (weather?.weather_summary as string) || "";
  const totalCost = hasLive
    ? liveStops!.reduce((sum, s) => sum + (s.estimated_cost || 0), 0)
    : 60;
  const currency = hasLive && liveStops!.length > 0 ? liveStops![0].currency : "EUR";
  const maxDay = hasLive ? Math.max(...liveStops!.map((s) => s.day)) : 1;

  return (
    <div className="h-full overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_18px_45px_rgba(15,23,42,.1)]">
      <div className="border-b border-slate-100 bg-slate-950 px-5 py-4 text-white">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-300" />
              {status}
            </div>
            <h2 className="text-lg font-bold">{hasLive ? "AI Itinerary" : "Day 1 itinerary"}</h2>
            <p className="text-sm text-slate-400">{hasLive ? `${stops.length} stops — selected: ${activeStop.name}` : `Apr 30, Paris — selected: ${activeStop.name}`}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-right">
            <div className="text-lg font-bold">{currency} {totalCost}</div>
            <div className="text-xs text-slate-400">Total cost</div>
          </div>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
          <div className="rounded-xl bg-white/10 p-2"><CalendarDays className="mb-1 h-4 w-4 text-blue-300" /> {hasLive ? `${maxDay} day${maxDay !== 1 ? "s" : ""}` : "7.5h plan"}</div>
          <div className="rounded-xl bg-white/10 p-2"><CloudSun className="mb-1 h-4 w-4 text-amber-300" /> {weatherStr || "18°C cloudy"}</div>
          <div className="rounded-xl bg-white/10 p-2"><Wallet className="mb-1 h-4 w-4 text-emerald-300" /> Budget OK</div>
        </div>
      </div>

      <div className="p-5">
        <div className="relative space-y-3">
          <div className="absolute bottom-8 left-[21px] top-8 w-px bg-gradient-to-b from-blue-300 via-violet-300 to-emerald-300" />
          {stops.map((stop) => {
            const isActive = activeStopId === stop.id;
            return (
              <button key={stop.id} onClick={() => onStopChange(stop.id)} className="relative flex w-full gap-3 text-left">
                <div className={`z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white shadow-lg ${isActive ? "bg-gradient-to-br from-blue-600 to-violet-600" : "bg-slate-300"}`}>
                  {stop.id}
                </div>
                <div className={`group flex-1 rounded-2xl border p-3 transition hover:-translate-y-0.5 hover:bg-white hover:shadow-lg ${isActive ? "border-blue-200 bg-blue-50" : "border-slate-100 bg-slate-50"}`}>
                  <div className="flex gap-3">
                    <img
                      src={hasLive ? placeImageUrl(stop.name) : `https://picsum.photos/seed/${stop.name.toLowerCase().replace(/\s+/g, "-")}-static/160/128`}
                      alt={stop.name}
                      className="h-16 w-20 shrink-0 rounded-xl object-cover"
                      onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; (e.currentTarget.nextSibling as HTMLElement).style.display = "block"; }}
                    />
                    <div className={`hidden h-16 w-20 shrink-0 rounded-xl bg-gradient-to-br ${stop.tint}`} />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-bold text-slate-950">{stop.name}</h3>
                          <span className="mt-1 inline-flex rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-blue-700">{stop.tag}</span>
                        </div>
                        <div className="text-right text-sm font-bold text-slate-900">{stop.cost}</div>
                      </div>
                      <div className="mt-2 grid grid-cols-4 gap-2 text-[11px] font-medium text-slate-500">
                        <span>{stop.time}</span>
                        <span>{stop.duration}</span>
                        <span>{stop.distance}</span>
                        <span className="flex items-center gap-1"><Train className="h-3 w-3" /> {stop.transport}</span>
                      </div>
                      <div className="mt-3 flex gap-1.5">
                        {actions.map((action) => {
                          const Icon = action.icon;
                          return (
                            <span
                              key={action.label}
                              onClick={(event) => {
                                event.stopPropagation();
                                onStopChange(stop.id);
                                setStatus(action.label);
                              }}
                              className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 hover:border-blue-200 hover:text-blue-600"
                            >
                              <Icon className="h-3.5 w-3.5" />
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
