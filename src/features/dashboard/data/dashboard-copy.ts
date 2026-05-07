import type { DashboardCopy, SupportedLanguage } from "../types/dashboard.types";

export const defaultDashboardCopy: DashboardCopy = {
    eyebrow: "Assistant-Controlled Workspace",
  title: "AI Travel Assistant",
  sync: "",
  body: ""
};

export const dashboardCopyByLanguage: Record<SupportedLanguage, DashboardCopy> = {
  English: defaultDashboardCopy,
  French: {
    eyebrow: "Espace controle par l'assistant",
    title: "Console mondiale de planification voyage generee par IA",
    body: "L'assistant met a jour l'itineraire, la carte, la traduction, le budget et les voyages enregistres.",
    sync: "Carte synchronisee avec l'assistant",
  },
  German: {
    eyebrow: "Vom Assistenten gesteuerter Arbeitsbereich",
    title: "KI generierte globale Reiseplanungskonsole",
    body: "Der Assistent aktualisiert Reiseplan, Route, Ubersetzung, Budget und gespeicherte Reisen.",
    sync: "Karte mit Assistent synchronisiert",
  },
  Spanish: {
    eyebrow: "Espacio controlado por el asistente",
    title: "Consola global de planificacion de viajes con IA",
    body: "El asistente actualiza itinerario, mapa, traduccion, presupuesto y viajes guardados.",
    sync: "Mapa sincronizado con el asistente",
  },
};

export const initialBookingPrices = {
  "Eiffel Tower summit ticket": 25,
  "Louvre timed entry": 17,
  "Seine river cruise": 18,
  "Metro day pass": 8,
};

export const optimizedBookingPrices = {
  "Eiffel Tower summit ticket": 22,
  "Louvre timed entry": 15,
  "Seine river cruise": 16,
  "Metro day pass": 7,
};
