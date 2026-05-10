export interface TripSummary {
  destination: string;
  duration_days: number;
  travelers: string;
  budget: number;
  currency: string;
  origin?: string;
}

export interface WeatherData {
  location: string;
  temperature: number;
  description: string;
  humidity: number;
  wind_speed: number;
}

export interface FlightData {
  origin: string;
  destination: string;
  departure_date: string;
  return_date?: string;
  price: string;
  airline: string;
}

export interface HotelData {
  name: string;
  location: string;
  price_per_night: string;
  rating: number;
}

export interface ItineraryItem {
  day: number;
  time: string;
  activity: string;
}

export interface BudgetBreakdown {
  transport: number;
  food: number;
  activities: number;
  accommodation: number;
  intercity_transport: number;
  currency: string;
  total_known_cost: number;
  within_budget: boolean;
}

export interface DashboardPayload {
  trip_summary?: TripSummary;
  weather?: { data?: WeatherData; status?: string };
  flights?: { data?: FlightData[]; status?: string };
  hotels?: { data?: HotelData[]; status?: string };
  itinerary?: ItineraryItem[];
  budget_breakdown?: BudgetBreakdown;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  time: string;
  detectedLang?: string;
  dashboard?: DashboardPayload | null;
  showDashboard?: boolean;
}
