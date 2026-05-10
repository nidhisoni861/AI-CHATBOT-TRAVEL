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

// ── Static label translations ─────────────────────────────────────────────────

type Labels = {
  tripSummary: string; destination: string; from: string; duration: string;
  days: string; budget: string; travelers: string; weather: string;
  humidity: string; wind: string; flights: string; transport: string;
  food: string; activities: string; accommodation: string;
  intercityTransport: string; total: string; withinBudget: string;
  overBudget: string; hotels: string; itinerary: string; day: string;
};

const LABELS: Record<string, Labels> = {
  en: { tripSummary: "Trip Summary", destination: "Destination", from: "From", duration: "Duration", days: "days", budget: "Budget", travelers: "Travelers", weather: "Weather", humidity: "Humidity", wind: "Wind", flights: "Flights", transport: "Transport", food: "Food", activities: "Activities", accommodation: "Accommodation", intercityTransport: "Intercity Transport", total: "Total", withinBudget: "Within budget ✓", overBudget: "Over budget ✗", hotels: "Hotels", itinerary: "Itinerary", day: "Day" },
  de: { tripSummary: "Reiseübersicht", destination: "Reiseziel", from: "Von", duration: "Dauer", days: "Tage", budget: "Budget", travelers: "Reisende", weather: "Wetter", humidity: "Luftfeuchtigkeit", wind: "Wind", flights: "Flüge", transport: "Transport", food: "Essen", activities: "Aktivitäten", accommodation: "Unterkunft", intercityTransport: "Fernverkehr", total: "Gesamt", withinBudget: "Im Budget ✓", overBudget: "Über Budget ✗", hotels: "Hotels", itinerary: "Reiseplan", day: "Tag" },
  hi: { tripSummary: "यात्रा सारांश", destination: "गंतव्य", from: "से", duration: "अवधि", days: "दिन", budget: "बजट", travelers: "यात्री", weather: "मौसम", humidity: "आर्द्रता", wind: "हवा", flights: "उड़ानें", transport: "परिवहन", food: "भोजन", activities: "गतिविधियाँ", accommodation: "आवास", intercityTransport: "अंतरनगर परिवहन", total: "कुल", withinBudget: "बजट में ✓", overBudget: "बजट से अधिक ✗", hotels: "होटल", itinerary: "यात्रा कार्यक्रम", day: "दिन" },
  fr: { tripSummary: "Résumé du voyage", destination: "Destination", from: "De", duration: "Durée", days: "jours", budget: "Budget", travelers: "Voyageurs", weather: "Météo", humidity: "Humidité", wind: "Vent", flights: "Vols", transport: "Transport", food: "Nourriture", activities: "Activités", accommodation: "Hébergement", intercityTransport: "Transport interurbain", total: "Total", withinBudget: "Dans le budget ✓", overBudget: "Hors budget ✗", hotels: "Hôtels", itinerary: "Itinéraire", day: "Jour" },
  es: { tripSummary: "Resumen del viaje", destination: "Destino", from: "Desde", duration: "Duración", days: "días", budget: "Presupuesto", travelers: "Viajeros", weather: "Clima", humidity: "Humedad", wind: "Viento", flights: "Vuelos", transport: "Transporte", food: "Comida", activities: "Actividades", accommodation: "Alojamiento", intercityTransport: "Transporte interurbano", total: "Total", withinBudget: "Dentro del presupuesto ✓", overBudget: "Sobre el presupuesto ✗", hotels: "Hoteles", itinerary: "Itinerario", day: "Día" },
  it: { tripSummary: "Riepilogo viaggio", destination: "Destinazione", from: "Da", duration: "Durata", days: "giorni", budget: "Budget", travelers: "Viaggiatori", weather: "Meteo", humidity: "Umidità", wind: "Vento", flights: "Voli", transport: "Trasporto", food: "Cibo", activities: "Attività", accommodation: "Alloggio", intercityTransport: "Trasporto intercity", total: "Totale", withinBudget: "Nel budget ✓", overBudget: "Fuori budget ✗", hotels: "Hotel", itinerary: "Itinerario", day: "Giorno" },
  pt: { tripSummary: "Resumo da viagem", destination: "Destino", from: "De", duration: "Duração", days: "dias", budget: "Orçamento", travelers: "Viajantes", weather: "Clima", humidity: "Humidade", wind: "Vento", flights: "Voos", transport: "Transporte", food: "Alimentação", activities: "Atividades", accommodation: "Alojamento", intercityTransport: "Transporte intercidades", total: "Total", withinBudget: "Dentro do orçamento ✓", overBudget: "Acima do orçamento ✗", hotels: "Hotéis", itinerary: "Itinerário", day: "Dia" },
  nl: { tripSummary: "Reisoverzicht", destination: "Bestemming", from: "Van", duration: "Duur", days: "dagen", budget: "Budget", travelers: "Reizigers", weather: "Weer", humidity: "Vochtigheid", wind: "Wind", flights: "Vluchten", transport: "Vervoer", food: "Eten", activities: "Activiteiten", accommodation: "Accommodatie", intercityTransport: "Intercityvervoer", total: "Totaal", withinBudget: "Binnen budget ✓", overBudget: "Boven budget ✗", hotels: "Hotels", itinerary: "Reisplan", day: "Dag" },
  ru: { tripSummary: "Сводка поездки", destination: "Направление", from: "Откуда", duration: "Продолжительность", days: "дней", budget: "Бюджет", travelers: "Путешественники", weather: "Погода", humidity: "Влажность", wind: "Ветер", flights: "Рейсы", transport: "Транспорт", food: "Питание", activities: "Активности", accommodation: "Проживание", intercityTransport: "Межгородской транспорт", total: "Итого", withinBudget: "В рамках бюджета ✓", overBudget: "Превышение бюджета ✗", hotels: "Отели", itinerary: "Маршрут", day: "День" },
  zh: { tripSummary: "行程摘要", destination: "目的地", from: "出发地", duration: "时长", days: "天", budget: "预算", travelers: "旅行者", weather: "天气", humidity: "湿度", wind: "风速", flights: "航班", transport: "交通", food: "餐饮", activities: "活动", accommodation: "住宿", intercityTransport: "城际交通", total: "合计", withinBudget: "在预算内 ✓", overBudget: "超出预算 ✗", hotels: "酒店", itinerary: "行程", day: "第" },
  ja: { tripSummary: "旅行概要", destination: "目的地", from: "出発地", duration: "期間", days: "日間", budget: "予算", travelers: "旅行者", weather: "天気", humidity: "湿度", wind: "風速", flights: "フライト", transport: "交通", food: "食費", activities: "アクティビティ", accommodation: "宿泊", intercityTransport: "都市間交通", total: "合計", withinBudget: "予算内 ✓", overBudget: "予算超過 ✗", hotels: "ホテル", itinerary: "旅程", day: "日" },
  ko: { tripSummary: "여행 요약", destination: "목적지", from: "출발지", duration: "기간", days: "일", budget: "예산", travelers: "여행자", weather: "날씨", humidity: "습도", wind: "바람", flights: "항공편", transport: "교통", food: "식비", activities: "활동", accommodation: "숙박", intercityTransport: "도시 간 교통", total: "합계", withinBudget: "예산 내 ✓", overBudget: "예산 초과 ✗", hotels: "호텔", itinerary: "여행 일정", day: "일" },
  ar: { tripSummary: "ملخص الرحلة", destination: "الوجهة", from: "من", duration: "المدة", days: "أيام", budget: "الميزانية", travelers: "المسافرون", weather: "الطقس", humidity: "الرطوبة", wind: "الرياح", flights: "الرحلات", transport: "المواصلات", food: "الطعام", activities: "الأنشطة", accommodation: "الإقامة", intercityTransport: "النقل بين المدن", total: "الإجمالي", withinBudget: "ضمن الميزانية ✓", overBudget: "تجاوز الميزانية ✗", hotels: "الفنادق", itinerary: "جدول الرحلة", day: "اليوم" },
  tr: { tripSummary: "Seyahat Özeti", destination: "Varış", from: "Nereden", duration: "Süre", days: "gün", budget: "Bütçe", travelers: "Yolcular", weather: "Hava Durumu", humidity: "Nem", wind: "Rüzgar", flights: "Uçuşlar", transport: "Ulaşım", food: "Yiyecek", activities: "Aktiviteler", accommodation: "Konaklama", intercityTransport: "Şehirlerarası Ulaşım", total: "Toplam", withinBudget: "Bütçe dahilinde ✓", overBudget: "Bütçe aşıldı ✗", hotels: "Oteller", itinerary: "Seyahat Planı", day: "Gün" },
  pl: { tripSummary: "Podsumowanie podróży", destination: "Cel podróży", from: "Skąd", duration: "Czas trwania", days: "dni", budget: "Budżet", travelers: "Podróżnicy", weather: "Pogoda", humidity: "Wilgotność", wind: "Wiatr", flights: "Loty", transport: "Transport", food: "Jedzenie", activities: "Atrakcje", accommodation: "Zakwaterowanie", intercityTransport: "Transport międzymiastowy", total: "Łącznie", withinBudget: "W budżecie ✓", overBudget: "Powyżej budżetu ✗", hotels: "Hotele", itinerary: "Plan podróży", day: "Dzień" },
};

function getLabels(lang = "en"): Labels {
  return LABELS[lang] ?? LABELS.en;
}

// ── Sub-cards ─────────────────────────────────────────────────────────────────

function TripCard({ s, t }: { s: TripSummary; t: Labels }) {
  return (
    <div className="rounded-2xl border border-teal-100 bg-gradient-to-br from-teal-50 to-cyan-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <MapPin className="h-3.5 w-3.5 text-teal-600" />
        <span className="text-xs font-bold text-teal-800">{t.tripSummary}</span>
      </div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        <div>
          <p className="text-slate-400">{t.destination}</p>
          <p className="font-semibold text-slate-800">{s.destination}</p>
        </div>
        {s.origin && (
          <div>
            <p className="text-slate-400">{t.from}</p>
            <p className="font-semibold text-slate-800">{s.origin}</p>
          </div>
        )}
        <div>
          <p className="text-slate-400">{t.duration}</p>
          <p className="font-semibold text-slate-800">{s.duration_days} {t.days}</p>
        </div>
        <div>
          <p className="text-slate-400">{t.budget}</p>
          <p className="font-semibold text-slate-800">{s.budget} {s.currency}</p>
        </div>
        {s.travelers && (
          <div className="col-span-2">
            <p className="text-slate-400">{t.travelers}</p>
            <p className="font-semibold capitalize text-slate-800">{s.travelers}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function WeatherCard({ w, t }: { w: WeatherData; t: Labels }) {
  return (
    <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50 to-sky-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Cloud className="h-3.5 w-3.5 text-blue-500" />
        <span className="text-xs font-bold text-blue-800">{t.weather}</span>
      </div>
      <p className="text-xl font-bold text-slate-800">{w.temperature.toFixed(1)}°C</p>
      <p className="mb-2 text-xs capitalize text-slate-500">{w.description}</p>
      <div className="grid grid-cols-2 gap-1 text-xs">
        <div>
          <p className="text-slate-400">{t.humidity}</p>
          <p className="font-semibold text-slate-800">{w.humidity}%</p>
        </div>
        <div>
          <p className="text-slate-400">{t.wind}</p>
          <p className="font-semibold text-slate-800">{w.wind_speed} m/s</p>
        </div>
      </div>
    </div>
  );
}

function FlightCard({ flights, t }: { flights: FlightData[]; t: Labels }) {
  return (
    <div className="rounded-2xl border border-purple-100 bg-gradient-to-br from-purple-50 to-violet-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Plane className="h-3.5 w-3.5 text-purple-600" />
        <span className="text-xs font-bold text-purple-800">
          {t.flights} ({flights.length})
        </span>
      </div>
      <div className="max-h-48 space-y-2 overflow-y-auto">
        {flights.map((f, i) => (
          <div key={i} className="space-y-0.5 border-b border-purple-100 pb-2 last:border-0 last:pb-0 text-xs">
            <p className="font-semibold text-slate-800">{f.origin} → {f.destination}</p>
            <p className="text-slate-500">
              {f.departure_date}{f.return_date ? ` – ${f.return_date}` : ""}
            </p>
            <div className="flex items-center justify-between">
              <p className="text-slate-500">{f.airline}</p>
              <p className="font-bold text-purple-700">{f.price}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function BudgetCard({ b, t }: { b: BudgetBreakdown; t: Labels }) {
  return (
    <div className="rounded-2xl border border-green-100 bg-gradient-to-br from-green-50 to-emerald-50 p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Wallet className="h-3.5 w-3.5 text-green-600" />
        <span className="text-xs font-bold text-green-800">{t.budget}</span>
      </div>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-slate-400">{t.transport}</span>
          <span className="font-semibold">{b.transport} {b.currency}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">{t.food}</span>
          <span className="font-semibold">{b.food} {b.currency}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">{t.activities}</span>
          <span className="font-semibold">{b.activities} {b.currency}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">{t.accommodation}</span>
          <span className="font-semibold">{b.accommodation} {b.currency}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">{t.intercityTransport}</span>
          <span className="font-semibold">{b.intercity_transport} {b.currency}</span>
        </div>
        <div className="flex justify-between border-t border-green-200 pt-1">
          <span className="font-bold text-slate-700">{t.total}</span>
          <span className="font-bold text-green-700">{b.total_known_cost} {b.currency}</span>
        </div>
        <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${b.within_budget ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
          {b.within_budget ? t.withinBudget : t.overBudget}
        </span>
      </div>
    </div>
  );
}

function HotelsCard({ hotels, t }: { hotels: HotelData[]; t: Labels }) {
  return (
    <div className="col-span-2 rounded-2xl border border-slate-200 bg-white p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Hotel className="h-3.5 w-3.5 text-amber-500" />
        <span className="text-xs font-bold text-slate-800">{t.hotels}</span>
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

function ItineraryCard({ items, t }: { items: ItineraryItem[]; t: Labels }) {
  const days = [...new Set(items.map((i) => i.day))].sort((a, b) => a - b);
  return (
    <div className="col-span-2 rounded-2xl border border-slate-200 bg-white p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <CalendarDays className="h-3.5 w-3.5 text-teal-600" />
        <span className="text-xs font-bold text-slate-800">{t.itinerary}</span>
      </div>
      <div className="space-y-2.5">
        {days.map((day) => (
          <div key={day}>
            <p className="mb-1 text-xs font-bold text-teal-700">{t.day} {day}</p>
            {items
              .filter((i) => i.day === day)
              .map((item, idx) => (
                <div key={idx} className="flex gap-2 text-xs">
                  <span className="w-16 shrink-0 font-medium text-slate-400">{item.time}</span>
                  <span className="text-slate-700">{item.activity}</span>
                </div>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main export ───────────────────────────────────────────────────────────────

export function DashboardCards({
  payload,
  lang = "en",
}: {
  payload: DashboardPayload;
  lang?: string;
}) {
  const t = getLabels(lang);

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
    payload.trip_summary || weather || flights || hotels || itinerary || payload.budget_breakdown;

  if (!hasAny) return null;

  return (
    <div className="mt-2 grid grid-cols-2 gap-2">
      {payload.trip_summary && <TripCard s={payload.trip_summary} t={t} />}
      {weather && <WeatherCard w={weather} t={t} />}
      {flights && <FlightCard flights={flights} t={t} />}
      {payload.budget_breakdown && <BudgetCard b={payload.budget_breakdown} t={t} />}
      {hotels && <HotelsCard hotels={hotels} t={t} />}
      {itinerary && <ItineraryCard items={itinerary} t={t} />}
    </div>
  );
}
