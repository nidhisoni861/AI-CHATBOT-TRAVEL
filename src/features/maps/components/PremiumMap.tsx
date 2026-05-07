import { LatLngExpression } from "leaflet";
import L from "leaflet";
import { useEffect, useMemo, useState } from "react";
import { Clock, Layers, LocateFixed, Minus, Navigation, Plus, Route, Sparkles } from "lucide-react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";
import { departureCity, destinationCity, tripStops } from "../data/paris-route";
import type { ItineraryStop } from "@/lib/api";

const numberIcon = (num: number, active = false) =>
  L.divIcon({
    className: "custom-marker",
    html: `<div style="background:${active ? "linear-gradient(135deg,#f97316,#facc15)" : "linear-gradient(135deg,#2563eb,#7c3aed)"};color:white;width:${active ? 44 : 34}px;height:${active ? 44 : 34}px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-weight:800;border:3px solid white;box-shadow:0 10px 24px rgba(37,99,235,.38);font-size:13px">${num}</div>`,
    iconSize: [active ? 44 : 34, active ? 44 : 34],
    iconAnchor: [active ? 22 : 17, active ? 22 : 17],
  });

function MapControls({ onLayerToggle, onStatus }: { onLayerToggle: () => void; onStatus: (status: string) => void }) {
  const map = useMap();
  const controls = [
    { icon: Plus, label: "Zoom in", action: () => { map.zoomIn(); onStatus("Zoomed in"); } },
    { icon: Minus, label: "Zoom out", action: () => { map.zoomOut(); onStatus("Zoomed out"); } },
    { icon: Layers, label: "Layers", action: () => { onLayerToggle(); onStatus("Map layer switched"); } },
    { icon: LocateFixed, label: "Locate", action: () => { map.flyTo(destinationCity, 13); onStatus("Centered on Paris"); } },
  ];

  return (
    <div className="absolute right-4 top-4 z-[1000] grid gap-2">
      {controls.map((control) => {
        const Icon = control.icon;
        return (
          <button
            key={control.label}
            onClick={control.action}
            title={control.label}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-lg hover:border-blue-200 hover:text-blue-700"
          >
            <Icon className="h-4 w-4" />
          </button>
        );
      })}
    </div>
  );
}

function FocusActiveStop({ activeStopId, stops }: { activeStopId: number; stops: typeof tripStops }) {
  const map = useMap();

  useEffect(() => {
    const stop = stops.find((item) => item.id === activeStopId);
    if (stop) map.flyTo(stop.position, 15, { duration: 0.8 });
  }, [activeStopId, map, stops]);

  return null;
}

interface PremiumMapProps {
  activeStopId: number;
  onStopFocus: (stopId: number) => void;
  liveStops?: ItineraryStop[];
}

export function PremiumMap({ activeStopId, onStopFocus, liveStops }: PremiumMapProps) {
  const hasLive = Array.isArray(liveStops) && liveStops.length > 0 && liveStops.some((s) => s.latitude !== 0 || s.longitude !== 0);

  const activeStops = hasLive
    ? liveStops!.map((s, i) => ({
        id: i + 1,
        name: s.name,
        category: s.type,
        position: [s.latitude, s.longitude] as LatLngExpression,
        visitTime: `Day ${s.day}`,
        duration: `${s.duration_minutes}min`,
        cost: `${s.currency} ${s.estimated_cost}`,
        transport: "",
        description: s.notes,
      }))
    : tripStops;

  const fallbackRoute = activeStops.map((stop) => stop.position);
  const [roadRoute, setRoadRoute] = useState<LatLngExpression[]>(fallbackRoute);
  const [useLightLayer, setUseLightLayer] = useState(false);
  const [status, setStatus] = useState(hasLive ? "Live AI route loaded" : "Road route loading from OSRM");
  const routeCoordinates = useMemo(
    () => activeStops.map((stop) => {
      const [lat, lng] = stop.position as [number, number];
      return `${lng},${lat}`;
    }).join(";"),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [hasLive ? liveStops?.map((s) => s.global_stop_id).join() : "static"],
  );
  const tileUrl = useLightLayer
    ? "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

  useEffect(() => {
    let isMounted = true;

    fetch(`https://router.project-osrm.org/route/v1/foot/${routeCoordinates}?overview=full&geometries=geojson`)
      .then((response) => response.json())
      .then((data) => {
        const coordinates = data?.routes?.[0]?.geometry?.coordinates;
        if (!isMounted || !Array.isArray(coordinates)) return;
        setRoadRoute(coordinates.map(([lng, lat]: [number, number]) => [lat, lng] as LatLngExpression));
        setStatus("Road-following route active");
      })
      .catch(() => {
        if (!isMounted) return;
        setRoadRoute(fallbackRoute);
        setStatus("Offline fallback route active");
      });

    return () => {
      isMounted = false;
    };
  }, [routeCoordinates]);

  return (
    <div className="overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_18px_45px_rgba(15,23,42,.1)]">
      <div className="flex items-center justify-between border-b border-slate-100 bg-white px-5 py-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-slate-950">{hasLive ? "AI-Generated Route" : "Paris Trip Route"}</h2>
            <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700">Route generated by AI</span>
          </div>
          <p className="mt-1 text-sm text-slate-500">{hasLive ? `${activeStops.length} stops from your request` : "Stuttgart (STR) → Paris (CDG)"}</p>
        </div>
        <div className="flex gap-2">
          {["Leaflet map connected", "4 stops optimized"].map((label) => (
            <span key={label} className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
              {label}
            </span>
          ))}
        </div>
      </div>

      <div className="relative h-[520px]">
        <div className="absolute left-4 top-4 z-[1000] rounded-2xl border border-white/70 bg-white/95 p-3 shadow-xl backdrop-blur">
          <div className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-900">
            <Route className="h-4 w-4 text-blue-600" />
            Route legend
          </div>
          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex items-center gap-2"><span className="w-10 border-t-2 border-dashed border-blue-500" /> Flight</div>
            <div className="flex items-center gap-2"><span className="h-1 w-10 rounded bg-blue-600" /> Metro</div>
            <div className="flex items-center gap-2"><span className="w-10 border-t-2 border-dotted border-emerald-500" /> Walking</div>
          </div>
        </div>

        <div className="absolute bottom-4 left-4 z-[1000] flex items-center gap-2 rounded-full border border-blue-100 bg-white/95 px-3 py-2 text-xs font-semibold text-blue-700 shadow-lg">
          <Sparkles className="h-4 w-4" />
          {status}
        </div>

        <MapContainer center={hasLive ? (activeStops[0].position as [number, number]) : [48.862, 2.337]} zoom={12} scrollWheelZoom className="h-full w-full">
          <FocusActiveStop activeStopId={activeStopId} stops={activeStops} />
          <MapControls onLayerToggle={() => setUseLightLayer((value) => !value)} onStatus={setStatus} />
          <TileLayer attribution='&copy; OpenStreetMap contributors' url={tileUrl} />
          <Polyline positions={[departureCity, destinationCity]} pathOptions={{ color: "#2563eb", weight: 2, dashArray: "9, 9", opacity: 0.65 }} />
          <Polyline positions={roadRoute} pathOptions={{ color: "#2563eb", weight: 5, opacity: 0.88, lineCap: "round", lineJoin: "round" }} />
          <Polyline positions={fallbackRoute.slice(1, 3)} pathOptions={{ color: "#10b981", weight: 4, dashArray: "1, 9", opacity: 0.9 }} />

          {activeStops.map((stop) => (
            <Marker
              key={stop.id}
              position={stop.position}
              icon={numberIcon(stop.id, activeStopId === stop.id)}
              eventHandlers={{ click: () => onStopFocus(stop.id) }}
            >
              <Popup>
                <div className="w-[250px] overflow-hidden rounded-xl bg-white">
                  <div className="h-24 bg-gradient-to-br from-blue-500 via-sky-300 to-amber-200" />
                  <div className="p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs font-bold text-white">Stop {stop.id}</span>
                      <span className="text-xs font-semibold text-slate-500">{stop.category}</span>
                    </div>
                    <div className="font-bold text-slate-950">{stop.name}</div>
                    <p className="mt-1 text-xs text-slate-600">{stop.description}</p>
                    <div className="mt-3 grid gap-1.5 text-xs text-slate-700">
                      <div className="flex items-center gap-2"><Clock className="h-3.5 w-3.5 text-blue-600" /> {stop.visitTime} - {stop.duration}</div>
                      <div>{stop.cost}</div>
                      <div className="flex items-center gap-2"><Navigation className="h-3.5 w-3.5 text-emerald-600" /> {stop.transport}</div>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
