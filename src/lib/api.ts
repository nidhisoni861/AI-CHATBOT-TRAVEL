const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

// ── Request / Response Types ────────────────────────────────────────────────

export type ModelMode = "base" | "fine_tuned" | "compare";

export interface ChatRequest {
  session_id: string;
  message: string;
  model_mode: ModelMode;
  language: string;
}

export interface ItineraryStop {
  global_stop_id: string;
  day: number;
  order: number;
  name: string;
  type: string;
  latitude: number;
  longitude: number;
  duration_minutes: number;
  estimated_cost: number;
  currency: string;
  notes: string;
}

export interface MapMarker {
  global_stop_id: string;
  label: string;
  name: string;
  latitude: number;
  longitude: number;
  popup_type: string;
}

export interface RouteSegment {
  from_stop_id: string;
  to_stop_id: string;
  mode: string;
  distance_km: number;
  duration_minutes: number;
  line_style: string;
  estimated_cost: number;
  currency: string;
}

export interface MapData {
  flight_path: Record<string, unknown>;
  markers: MapMarker[];
  route_segments: RouteSegment[];
}

export interface BudgetBreakdown {
  total: number;
  currency: string;
  flights: number;
  accommodation: number;
  food: number;
  activities: number;
  transport: number;
  misc: number;
}

export interface DashboardAction {
  action: string;
  target: string;
  status?: string;
}

export interface DashboardPayload {
  schema_version: "travel_dashboard_v1";
  intent: string;
  trip_summary: Record<string, unknown>;
  flight: Record<string, unknown>;
  stay_recommendations: unknown[];
  food_recommendations: unknown[];
  itinerary: ItineraryStop[];
  map_data: MapData;
  budget_breakdown: Partial<BudgetBreakdown>;
  dashboard_actions: DashboardAction[];
}

export interface ChatResponse {
  session_id: string;
  assistant_message: string;
  dashboard_payload: DashboardPayload;
  model_mode: ModelMode;
  reply: string;
  comparison?: Record<string, unknown>;
  tool_calls: unknown[];
  citations: string[];
}

// ── Schema Normalizer ───────────────────────────────────────────────────────
// Model sometimes returns nested [{day, stops:[]}] instead of flat ItineraryStop[]

interface NestedDay {
  day: number;
  stops: Omit<ItineraryStop, "day">[];
}

export function normalizeItinerary(raw: unknown): ItineraryStop[] {
  if (!Array.isArray(raw) || raw.length === 0) return [];
  const first = raw[0] as Record<string, unknown>;
  // Nested format: [{day: 1, stops: [...]}]
  if (typeof first.day === "number" && Array.isArray(first.stops)) {
    const nested = raw as NestedDay[];
    return nested.flatMap((dayObj, di) =>
      dayObj.stops.map((stop, si) => ({
        global_stop_id: (stop as ItineraryStop).global_stop_id ?? `stop_${di}_${si}`,
        day: dayObj.day,
        order: (stop as ItineraryStop).order ?? si + 1,
        name: (stop as ItineraryStop).name ?? "",
        type: (stop as ItineraryStop).type ?? "attraction",
        latitude: Number((stop as ItineraryStop).latitude) || 0,
        longitude: Number((stop as ItineraryStop).longitude) || 0,
        duration_minutes: (stop as ItineraryStop).duration_minutes ?? 60,
        estimated_cost: (stop as ItineraryStop).estimated_cost ?? 0,
        currency: (stop as ItineraryStop).currency ?? "EUR",
        notes: (stop as ItineraryStop).notes ?? "",
      }))
    );
  }
  // Flat format: already ItineraryStop[]
  return (raw as ItineraryStop[]).map((s, i) => ({
    ...s,
    global_stop_id: s.global_stop_id ?? `stop_${i}`,
    latitude: Number(s.latitude) || 0,
    longitude: Number(s.longitude) || 0,
  }));
}

// ── API Calls ───────────────────────────────────────────────────────────────

export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json() as Promise<ChatResponse>;
}

export async function resetSession(sessionId: string): Promise<void> {
  await fetch(`${BACKEND_URL}/chat/${sessionId}`, { method: "DELETE" });
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BACKEND_URL}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}
