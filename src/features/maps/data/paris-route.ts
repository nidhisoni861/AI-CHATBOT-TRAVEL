import type { LatLngExpression } from "leaflet";

export type TripStop = {
  id: number;
  name: string;
  category: string;
  position: LatLngExpression;
  visitTime: string;
  duration: string;
  cost: string;
  transport: string;
  description: string;
};

export const tripStops: TripStop[] = [
  {
    id: 1,
    name: "Eiffel Tower",
    category: "Landmark",
    position: [48.8584, 2.2945],
    visitTime: "09:00",
    duration: "2h",
    cost: "EUR 25",
    transport: "Metro to Louvre, 18 min",
    description: "Iconic morning viewpoint with reserved lift access.",
  },
  {
    id: 2,
    name: "Louvre Museum",
    category: "Museum",
    position: [48.8606, 2.3376],
    visitTime: "12:00",
    duration: "3h",
    cost: "EUR 17",
    transport: "Walk to Seine, 12 min",
    description: "Curated art route focused on culture and low queue time.",
  },
  {
    id: 3,
    name: "Seine River Cruise",
    category: "Experience",
    position: [48.8561, 2.3418],
    visitTime: "16:00",
    duration: "1h",
    cost: "EUR 18",
    transport: "Metro to Montmartre, 24 min",
    description: "Late afternoon cruise timed for softer light.",
  },
  {
    id: 4,
    name: "Montmartre",
    category: "Neighborhood",
    position: [48.8867, 2.3431],
    visitTime: "18:30",
    duration: "1.5h",
    cost: "Free",
    transport: "Walk local food spots",
    description: "Sunset view, artist square, and budget dinner options.",
  },
];

export const departureCity: LatLngExpression = [48.6908, 9.221];
export const destinationCity: LatLngExpression = [48.8566, 2.3522];
