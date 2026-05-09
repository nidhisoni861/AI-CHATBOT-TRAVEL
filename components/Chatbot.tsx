"use client";

import Image from "next/image";
import { useRef, useState, useEffect, KeyboardEvent } from "react";
import {
  Camera,
  CalendarDays,
  CheckCheck,
  Cloud,
  Hotel,
  MapPin,
  Mic,
  Paperclip,
  Plane,
  Plus,
  Send,
  Sparkles,
  Star,
  Utensils,
  Wallet,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface TripSummary {
  destination: string;
  duration_days: number;
  travelers: string;
  budget: number;
  currency: string;
  origin?: string;
}

interface WeatherData {
  location: string;
  temperature: number;
  description: string;
  humidity: number;
  wind_speed: number;
}

interface FlightData {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  price: string;
  airline: string;
}

interface HotelData {
  name: string;
  location: string;
  price_per_night: string;
  rating: number;
}

interface ItineraryItem {
  day: number;
  time: string;
  activity: string;
}

interface BudgetBreakdown {
  transport: number;
  food: number;
  activities: number;
  currency: string;
  total_known_cost: number;
  within_budget: boolean;
}

interface DashboardPayload {
  trip_summary?: TripSummary;
  weather?: { data?: WeatherData; status?: string };
  flights?: { data?: FlightData[]; status?: string };
  hotels?: { data?: HotelData[]; status?: string };
  itinerary?: ItineraryItem[];
  budget_breakdown?: BudgetBreakdown;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  time: string;
  dashboard?: DashboardPayload | null;
}

// ─── Dashboard Sub-cards ──────────────────────────────────────────────────────

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
            <p className="font-semibold capitalize text-slate-800">
              {s.travelers}
            </p>
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
      <div className="text-xs space-y-1">
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

function DashboardCards({ payload }: { payload: DashboardPayload }) {
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

// ─── Typing Indicator ─────────────────────────────────────────────────────────

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 animate-bounce rounded-full bg-teal-400"
          style={{ animationDelay: `${i * 0.15}s` }}
        />
      ))}
    </div>
  );
}

// ─── Suggestions ─────────────────────────────────────────────────────────────

const SUGGESTIONS = [
  { Icon: CalendarDays, label: "1 Day trip to Berlin" },
  { Icon: CalendarDays, label: "3 day trip to Munich with faster pace" },
  { Icon: Utensils, label: "5 day trip to Stuttgart with more food experiences" },
];

// ─── Main Component ───────────────────────────────────────────────────────────

export default function ChatBotPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "init",
      role: "assistant",
      text: "New chat started ✨\n\nTell me your destination, travel dates, budget, and travel style. I'll build your trip plan.",
      time: new Date().toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef(`session-${Date.now()}`);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    const now = () =>
      new Date().toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      });

    setMessages((prev) => [
      ...prev,
      { id: `u-${Date.now()}`, role: "user", text: msg, time: now() },
    ]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: sessionId.current }),
      });

      if (!res.ok) throw new Error("Backend error");

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text:
            data.assistant_message ??
            "I couldn't process that. Please try again.",
          time: now(),
          dashboard: data.dashboard_payload ?? null,
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: "assistant",
          text: "Something went wrong. Please check if the backend is running.",
          time: now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <section className="flex h-full max-h-[calc(100vh-128px)] min-h-0 w-full max-w-[1220px] flex-col rounded-[28px] border border-white/75 bg-white/80 p-4 shadow-[0_28px_90px_rgba(15,23,42,0.24)] backdrop-blur-2xl sm:rounded-[34px] sm:p-5 lg:p-6">
      {/* Header */}
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-100 to-white shadow-[0_12px_28px_rgba(20,184,166,0.28)] sm:h-14 sm:w-14">
            <div className="absolute inset-0 rounded-full border-[3px] border-cyan-100/80" />
            <Image
              src="/avatar.jpeg"
              alt="AI avatar"
              width={44}
              height={44}
              className="relative h-full w-full rounded-full object-cover"
              priority
            />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-xl font-bold tracking-tight text-slate-950 sm:text-2xl">
                Roamora AI
              </h1>
              <Sparkles className="h-5 w-5 text-teal-500" />
            </div>
            <p className="mt-0.5 text-xs font-medium text-slate-500 sm:text-sm">
              Your intelligent travel companion
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-white/80 bg-teal-700 px-3 py-2 text-white shadow-[0_10px_24px_rgba(13,148,136,0.35)] sm:gap-3 sm:px-4 sm:py-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20 sm:h-8 sm:w-8">
            <Mic className="h-4 w-4" />
          </span>
          <span className="hidden text-xs font-bold sm:inline sm:text-sm">
            Voice On
          </span>
          <span className="relative h-6 w-11 rounded-full bg-white/30">
            <span className="absolute left-5 top-0.5 h-5 w-5 rounded-full bg-white shadow-md" />
          </span>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="mt-4 flex flex-1 flex-col gap-3 overflow-y-auto pr-1 sm:mt-5">
        {messages.map((msg) =>
          msg.role === "user" ? (
            <div key={msg.id} className="flex justify-end">
              <div className="max-w-[80%] rounded-[18px] rounded-tr-md bg-gradient-to-br from-teal-700 to-cyan-700 px-4 py-3 text-white shadow-[0_10px_24px_rgba(13,148,136,0.28)] sm:max-w-[480px] sm:px-5">
                <p className="text-sm font-medium leading-relaxed">{msg.text}</p>
                <div className="mt-1.5 flex items-center justify-end gap-1.5 text-xs text-white/80">
                  <span>{msg.time}</span>
                  <CheckCheck className="h-3.5 w-3.5" />
                </div>
              </div>
            </div>
          ) : (
            <div key={msg.id} className="flex items-start gap-2.5 sm:gap-3">
              <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cyan-50 shadow-[0_8px_20px_rgba(20,184,166,0.22)] sm:h-10 sm:w-10">
                <Image
                  src="/avatar.jpeg"
                  alt="AI avatar"
                  width={36}
                  height={36}
                  className="h-full w-full rounded-full object-cover"
                />
              </div>
              <div className="min-w-0 max-w-[85%] flex-1 sm:max-w-[680px]">
                <div className="rounded-[18px] rounded-tl-md bg-white px-4 py-3 shadow-[0_10px_30px_rgba(15,23,42,0.10)] sm:px-5 sm:py-4">
                  <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">
                    {msg.text}
                  </p>
                  <p className="mt-2 text-right text-xs font-medium text-slate-400">
                    {msg.time}
                  </p>
                </div>
                {msg.dashboard && <DashboardCards payload={msg.dashboard} />}
              </div>
            </div>
          )
        )}

        {loading && (
          <div className="flex items-start gap-2.5 sm:gap-3">
            <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cyan-50 shadow-[0_8px_20px_rgba(20,184,166,0.22)] sm:h-10 sm:w-10">
              <Image
                src="/avatar.jpeg"
                alt="AI avatar"
                width={36}
                height={36}
                className="h-full w-full rounded-full object-cover"
              />
            </div>
            <div className="rounded-[18px] rounded-tl-md bg-white shadow-[0_10px_30px_rgba(15,23,42,0.10)]">
              <TypingIndicator />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestion Chips */}
      <div className="mt-4 flex flex-wrap justify-center gap-2 sm:gap-3">
        {SUGGESTIONS.map(({ Icon, label }) => (
          <button
            key={label}
            onClick={() => sendMessage(label)}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-full border border-teal-500/70 bg-white/60 px-3 py-2 text-xs font-semibold text-teal-700 shadow-sm transition hover:bg-white/90 disabled:opacity-50 sm:px-4 sm:py-2.5 sm:text-sm"
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <footer className="mt-4 rounded-[22px] border border-white/70 bg-white/75 p-1.5 shadow-[0_12px_40px_rgba(15,23,42,0.08)] sm:mt-5 sm:p-2">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            aria-label="Add"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-slate-700 shadow-sm sm:h-11 sm:w-11"
          >
            <Plus className="h-5 w-5" />
          </button>
          <button
            type="button"
            aria-label="Attach files"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-slate-600 sm:h-11 sm:w-11"
          >
            <Paperclip className="h-5 w-5" />
          </button>
          <button
            type="button"
            aria-label="Camera"
            className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-full text-slate-600 sm:flex sm:h-11 sm:w-11"
          >
            <Camera className="h-5 w-5" />
          </button>

          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask anything about travel..."
            rows={1}
            disabled={loading}
            className="min-w-0 flex-1 resize-none bg-transparent px-2 text-sm font-medium text-slate-800 placeholder-slate-400 focus:outline-none disabled:opacity-50"
          />

          <button
            type="button"
            aria-label="Voice input"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-slate-700 shadow-sm sm:h-11 sm:w-11"
          >
            <Mic className="h-5 w-5" />
          </button>
          <button
            type="button"
            aria-label="Send message"
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-700 to-cyan-700 text-white shadow-[0_10px_24px_rgba(13,148,136,0.35)] transition disabled:opacity-50 sm:h-12 sm:w-12"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </footer>
    </section>
  );
}
