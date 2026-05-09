import {
  CalendarDays,
  Cloud,
  Hotel,
  MapPin,
  Plane,
  Star,
  Wallet,
} from "lucide-react";
import type {
  BudgetBreakdown,
  DashboardPayload,
  FlightData,
  HotelData,
  ItineraryItem,
  TripSummary,
  WeatherData,
} from "./types";

function TripCard({ s }: { s: TripSummary }) {
  return (
    <div className="rounded-2xl border border-teal-100 bg-gradient-to-br from-teal-50 to-cyan-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <MapPin className="h-3.5 w-3.5 text-teal-600" />
        <span className="text-xs font-bold text-teal-800">Trip Summary</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        <div>
          <p className="text-slate-400">Destination</p>
          <p className="font-semibold text-slate-800">{s.destination}</p>
        </div>
        {s.origin && (
          <div>
            <p className="text-slate-400">From</p>
            <p className="font-semibold text-slate-800">{s.origin}</p>
          </div>
        )}
        <div>
          <p className="text-slate-400">Duration</p>
          <p className="font-semibold text-slate-800">{s.duration_days} days</p>
        </div>
        <div>
          <p className="text-slate-400">Budget</p>
          <p className="font-semibold text-slate-800">
            {s.budget} {s.currency}
          </p>
        </div>
        {s.travelers && (
          <div className="col-span-2">
            <p className="text-slate-400">Travelers</p>
            <p className="font-semibold capitalize text-slate-800">{s.travelers}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function WeatherCard({ w }: { w: WeatherData }) {
  return (
    <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-sky-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Cloud className="h-3.5 w-3.5 text-blue-500" />
        <span className="text-xs font-bold text-blue-800">Weather</span>
      </div>
      <p className="text-xl font-bold text-slate-800">
        {w.temperature.toFixed(1)}°C
      </p>
      <p className="mb-2 text-xs capitalize text-slate-500">{w.description}</p>
      <div className="grid grid-cols-2 gap-1 text-xs">
        <div>
          <p className="text-slate-400">Humidity</p>
          <p className="font-semibold text-slate-800">{w.humidity}%</p>
        </div>
        <div>
          <p className="text-slate-400">Wind</p>
          <p className="font-semibold text-slate-800">{w.wind_speed} m/s</p>
        </div>
      </div>
    </div>
  );
}

function FlightCard({ flights }: { flights: FlightData[] }) {
  const f = flights[0];
  return (
    <div className="rounded-2xl border border-purple-100 bg-gradient-to-br from-purple-50 to-violet-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Plane className="h-3.5 w-3.5 text-purple-600" />
        <span className="text-xs font-bold text-purple-800">Flights</span>
      </div>
      <div className="space-y-1 text-xs">
        <p className="font-semibold text-slate-800">
          {f.origin} → {f.destination}
        </p>
        <p className="text-slate-500">
          {f.departure_date}
          {f.return_date ? ` – ${f.return_date}` : ""}
        </p>
        <p className="font-bold text-purple-700">{f.price}</p>
        <p className="text-slate-500">{f.airline}</p>
      </div>
    </div>
  );
}

function BudgetCard({ b }: { b: BudgetBreakdown }) {
  return (
    <div className="rounded-2xl border border-green-100 bg-gradient-to-br from-green-50 to-emerald-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Wallet className="h-3.5 w-3.5 text-green-600" />
        <span className="text-xs font-bold text-green-800">Budget</span>
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-400">Transport</span>
          <span className="font-semibold">
            {b.transport} {b.currency}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Food</span>
          <span className="font-semibold">
            {b.food} {b.currency}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Activities</span>
          <span className="font-semibold">
            {b.activities} {b.currency}
          </span>
        </div>
        <div className="flex justify-between border-t border-green-200 pt-1">
          <span className="font-bold text-slate-700">Total</span>
          <span className="font-bold text-green-700">
            {b.total_known_cost} {b.currency}
          </span>
        </div>
        <span
          className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
            b.within_budget
              ? "bg-green-100 text-green-700"
              : "bg-red-100 text-red-700"
          }`}
        >
          {b.within_budget ? "Within budget ✓" : "Over budget ✗"}
        </span>
      </div>
    </div>
  );
}

function HotelsCard({ hotels }: { hotels: HotelData[] }) {
  return (
    <div className="col-span-2 rounded-2xl border border-slate-200 bg-white p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Hotel className="h-3.5 w-3.5 text-amber-500" />
        <span className="text-xs font-bold text-slate-800">Hotels</span>
      </div>
      <div className="max-h-36 space-y-1.5 overflow-y-auto">
        {hotels.slice(0, 6).map((h, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <span className="flex-1 truncate pr-2 text-slate-700">{h.name}</span>
            <div className="flex shrink-0 items-center gap-0.5">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              <span className="font-semibold text-slate-700">{h.rating}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ItineraryCard({ items }: { items: ItineraryItem[] }) {
  const days = [...new Set(items.map((i) => i.day))].sort((a, b) => a - b);
  return (
    <div className="col-span-2 rounded-2xl border border-slate-200 bg-white p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <CalendarDays className="h-3.5 w-3.5 text-teal-600" />
        <span className="text-xs font-bold text-slate-800">Itinerary</span>
      </div>
      <div className="space-y-2.5">
        {days.map((day) => (
          <div key={day}>
            <p className="mb-1 text-xs font-bold text-teal-700">Day {day}</p>
            {items
              .filter((i) => i.day === day)
              .map((item, idx) => (
                <div key={idx} className="flex gap-2 text-xs">
                  <span className="w-16 shrink-0 font-medium text-slate-400">
                    {item.time}
                  </span>
                  <span className="text-slate-700">{item.activity}</span>
                </div>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function DashboardCards({ payload }: { payload: DashboardPayload }) {
  const weather =
    payload.weather?.status === "available" && payload.weather.data
      ? payload.weather.data
      : null;
  const flights =
    payload.flights?.status === "available" && payload.flights.data?.length
      ? payload.flights.data
      : null;
  const hotels =
    payload.hotels?.status === "available" && payload.hotels.data?.length
      ? payload.hotels.data
      : null;
  const itinerary = payload.itinerary?.length ? payload.itinerary : null;

  const hasAny =
    payload.trip_summary ||
    weather ||
    flights ||
    hotels ||
    itinerary ||
    payload.budget_breakdown;

  if (!hasAny) return null;

  return (
    <div className="mt-2 grid grid-cols-2 gap-2">
      {payload.trip_summary && <TripCard s={payload.trip_summary} />}
      {weather && <WeatherCard w={weather} />}
      {flights && <FlightCard flights={flights} />}
      {payload.budget_breakdown && <BudgetCard b={payload.budget_breakdown} />}
      {hotels && <HotelsCard hotels={hotels} />}
      {itinerary && <ItineraryCard items={itinerary} />}
    </div>
  );
}
