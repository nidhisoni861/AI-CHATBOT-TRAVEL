import { useState } from "react";
import { ArrowUpRight, Calendar, CheckCircle2, MapPin, Sparkles } from "lucide-react";

const TINTS = ["from-blue-500 to-sky-400", "from-violet-500 to-fuchsia-400", "from-rose-500 to-orange-400", "from-emerald-500 to-teal-400", "from-amber-500 to-orange-400", "from-cyan-500 to-blue-400"];

const STATIC_TRIPS = [
  { destination: "Paris, France", dates: "Apr 30 - May 5", status: "Active", budget: "EUR 1,420", days: "5 days", tint: TINTS[0], isLive: false },
  { destination: "Rome, Italy", dates: "Jun 10 - Jun 14", status: "Planned", budget: "EUR 1,180", days: "4 days", tint: TINTS[1], isLive: false },
  { destination: "Tokyo, Japan", dates: "Sep 3 - Sep 10", status: "Draft", budget: "EUR 2,760", days: "7 days", tint: TINTS[2], isLive: false },
  { destination: "Barcelona, Spain", dates: "Oct 18 - Oct 22", status: "Draft", budget: "EUR 980", days: "4 days", tint: TINTS[3], isLive: false },
];

export interface SavedTrip {
  destination: string;
  dates: string;
  status: string;
  budget: string;
  days: string;
  tint: string;
  isLive: boolean;
}

interface SavedTripsWidgetProps {
  liveTrips?: SavedTrip[];
}

export function SavedTripsWidget({ liveTrips = [] }: SavedTripsWidgetProps) {
  const trips = [...liveTrips, ...STATIC_TRIPS];
  const [selectedTrip, setSelectedTrip] = useState(trips[0]);
  const [opened, setOpened] = useState(false);

  return (
    <div className="overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_18px_45px_rgba(15,23,42,.1)]">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <div className="mb-1 text-xs font-semibold text-emerald-700">{opened ? "Trip opened" : "Saved to trip"}</div>
          <h2 className="text-lg font-bold text-slate-950">Saved Trips</h2>
        </div>
        <button onClick={() => setOpened((value) => !value)} className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:border-blue-200 hover:text-blue-700">
          {opened ? "Close" : "Open"}
        </button>
      </div>
      <div className="grid grid-cols-2 gap-3 p-5">
        {trips.map((trip) => {
          const isSelected = selectedTrip.destination === trip.destination;
          return (
            <button
              key={trip.destination}
              onClick={() => {
                setSelectedTrip(trip);
                setOpened(true);
              }}
              className={`group flex items-center gap-3 rounded-2xl border p-3 text-left transition hover:bg-white hover:shadow-lg ${
                isSelected ? "border-blue-200 bg-blue-50" : "border-slate-100 bg-slate-50"
              }`}
            >
              <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${trip.tint} text-white shadow-lg`}>
                <MapPin className="h-5 w-5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1">
                  <h3 className="truncate text-sm font-bold text-slate-950">{trip.destination}</h3>
                  {trip.isLive && <Sparkles className="h-3 w-3 shrink-0 text-violet-500" />}
                </div>
                <div className="mt-1 flex items-center gap-1 text-xs text-slate-500">
                  <Calendar className="h-3 w-3" />
                  {trip.dates}
                </div>
                <span className={`mt-2 inline-flex rounded-full px-2 py-0.5 text-[11px] font-bold ${trip.isLive ? "bg-violet-100 text-violet-700" : trip.status === "Active" ? "bg-emerald-100 text-emerald-700" : trip.status === "Planned" ? "bg-blue-100 text-blue-700" : "bg-slate-200 text-slate-600"}`}>
                  {trip.isLive ? "AI" : trip.status}
                </span>
              </div>
              <ArrowUpRight className="h-4 w-4 shrink-0 text-slate-400 group-hover:text-blue-600" />
            </button>
          );
        })}
      </div>

      {opened && (
        <div className="mx-5 mb-5 rounded-2xl border border-blue-100 bg-blue-50 p-4">
          <div className="mb-2 flex items-center gap-2 text-sm font-bold text-blue-800">
            <CheckCircle2 className="h-4 w-4" />
            {selectedTrip.destination} workspace opened
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs font-semibold text-slate-600">
            <span className="rounded-xl bg-white px-3 py-2">{selectedTrip.days}</span>
            <span className="rounded-xl bg-white px-3 py-2">{selectedTrip.budget}</span>
            <span className="rounded-xl bg-white px-3 py-2">{selectedTrip.status}</span>
          </div>
        </div>
      )}
    </div>
  );
}
