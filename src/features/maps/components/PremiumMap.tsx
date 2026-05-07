"use client";

import { LatLngExpression } from "leaflet";
import L from "leaflet";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Clock,
  Layers,
  LocateFixed,
  Minus,
  Navigation,
  Plus,
  Route,
  Sparkles,
} from "lucide-react";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import { departureCity, destinationCity, tripStops } from "../data/paris-route";
import type { ItineraryStop } from "../../../lib/api";

type RouteStop = {
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

const numberIcon = (num: number, active = false) =>
  L.divIcon({
    className: "custom-marker",
    html: `
      <div style="
        background:${
          active
            ? "linear-gradient(135deg,#f97316,#facc15)"
            : "linear-gradient(135deg,#2563eb,#7c3aed)"
        };
        color:white;
        width:${active ? 38 : 30}px;
        height:${active ? 38 : 30}px;
        border-radius:999px;
        display:flex;
        align-items:center;
        justify-content:center;
        font-weight:800;
        border:3px solid white;
        box-shadow:0 8px 20px rgba(37,99,235,.32);
        font-size:12px;
      ">
        ${num}
      </div>
    `,
    iconSize: [active ? 38 : 30, active ? 38 : 30],
    iconAnchor: [active ? 19 : 15, active ? 19 : 15],
  });

function MapControls({
  onLayerToggle,
  onStatus,
}: {
  onLayerToggle: () => void;
  onStatus: (status: string) => void;
}) {
  const map = useMap();

  const controls = [
    {
      icon: Plus,
      label: "Zoom in",
      action: () => {
        map.zoomIn();
        onStatus("Zoomed in");
      },
    },
    {
      icon: Minus,
      label: "Zoom out",
      action: () => {
        map.zoomOut();
        onStatus("Zoomed out");
      },
    },
    {
      icon: Layers,
      label: "Layers",
      action: () => {
        onLayerToggle();
        onStatus("Map layer switched");
      },
    },
    {
      icon: LocateFixed,
      label: "Locate",
      action: () => {
        map.flyTo(destinationCity, 13);
        onStatus("Centered on Paris");
      },
    },
  ];

  return (
    <div className="absolute right-3 top-3 z-[1000] grid gap-1.5">
      {controls.map((control) => {
        const Icon = control.icon;

        return (
          <button
            key={control.label}
            onClick={control.action}
            title={control.label}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-md transition hover:border-blue-200 hover:text-blue-700"
          >
            <Icon className="h-3.5 w-3.5" />
          </button>
        );
      })}
    </div>
  );
}

function FocusActiveStop({
  activeStopId,
  stops,
}: {
  activeStopId: number;
  stops: RouteStop[];
}) {
  const map = useMap();
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;

    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    if (!isMounted.current) return;

    const stop = stops.find((item) => item.id === activeStopId);
    if (!stop) return;

    try {
      const container = map.getContainer();

      if (!container || !document.body.contains(container)) return;

      map.flyTo(stop.position, 15, { duration: 0.8 });
    } catch {
      // Map not ready or already destroyed.
    }
  }, [activeStopId, map, stops]);

  return null;
}

interface PremiumMapProps {
  activeStopId: number;
  onStopFocus: (stopId: number) => void;
  liveStops?: ItineraryStop[];
}

export function PremiumMap({
  activeStopId,
  onStopFocus,
  liveStops,
}: PremiumMapProps) {
  const hasLive =
    Array.isArray(liveStops) &&
    liveStops.length > 0 &&
    liveStops.some((stop) => stop.latitude !== 0 || stop.longitude !== 0);

  const activeStops: RouteStop[] = useMemo(() => {
    if (hasLive) {
      return liveStops!.map((stop, index) => ({
        id: index + 1,
        name: stop.name,
        category: stop.type,
        position: [stop.latitude, stop.longitude] as LatLngExpression,
        visitTime: `Day ${stop.day}`,
        duration: `${stop.duration_minutes} min`,
        cost: `${stop.currency} ${stop.estimated_cost}`,
        transport: "",
        description: stop.notes,
      }));
    }

    return tripStops as RouteStop[];
  }, [hasLive, liveStops]);

  const fallbackRoute = useMemo(
    () => activeStops.map((stop) => stop.position),
    [activeStops]
  );

  const [roadRoute, setRoadRoute] =
    useState<LatLngExpression[]>(fallbackRoute);

  const [useLightLayer, setUseLightLayer] = useState(false);
  const [status, setStatus] = useState(
    hasLive ? "Live AI route loaded" : "Road route loading from OSRM"
  );

  const mapKey = useMemo(() => {
    if (!hasLive) return "static";

    return `live-${liveStops!
      .map((stop) => stop.global_stop_id ?? stop.name)
      .join("-")}`;
  }, [hasLive, liveStops]);

  const routeCoordinates = useMemo(
    () =>
      activeStops
        .map((stop) => {
          const [lat, lng] = stop.position as [number, number];
          return `${lng},${lat}`;
        })
        .join(";"),
    [activeStops]
  );

  const tileUrl = useLightLayer
    ? "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
    : "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

  useEffect(() => {
    let isMounted = true;

    setStatus(hasLive ? "Live AI route loaded" : "Road route loading from OSRM");

    fetch(
      `https://router.project-osrm.org/route/v1/foot/${routeCoordinates}?overview=full&geometries=geojson`
    )
      .then((response) => response.json())
      .then((data) => {
        const coordinates = data?.routes?.[0]?.geometry?.coordinates;

        if (!isMounted || !Array.isArray(coordinates)) return;

        setRoadRoute(
          coordinates.map(
            ([lng, lat]: [number, number]) => [lat, lng] as LatLngExpression
          )
        );

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
  }, [routeCoordinates, fallbackRoute, hasLive]);

  return (
    <div className="overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_14px_34px_rgba(15,23,42,.08)]">
      {/* Compact Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-white px-4 py-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-base font-extrabold text-slate-950 sm:text-lg">
              {hasLive ? "AI-Generated Route" : "Paris Trip Route"}
            </h2>

            <span className="rounded-full bg-blue-50 px-2.5 py-1 text-[11px] font-bold text-blue-700">
              Route generated by AI
            </span>
          </div>

          <p className="mt-1 text-xs font-medium text-slate-500 sm:text-sm">
            {hasLive
              ? `${activeStops.length} stops from your request`
              : "Stuttgart (STR) → Paris (CDG)"}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <span className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-[11px] font-bold text-emerald-700">
            Leaflet connected
          </span>

          <span className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1 text-[11px] font-bold text-emerald-700">
            {activeStops.length} stops optimized
          </span>
        </div>
      </div>

      {/* Smaller Map Height */}
      <div className="relative h-[320px] overflow-hidden sm:h-[350px] lg:h-[380px] xl:h-[400px]">
        {/* Route Legend */}
        <div className="absolute left-3 top-3 z-[1000] rounded-2xl border border-white/70 bg-white/95 p-2.5 shadow-lg backdrop-blur">
          <div className="mb-2 flex items-center gap-2 text-xs font-extrabold text-slate-900">
            <Route className="h-3.5 w-3.5 text-blue-600" />
            Route legend
          </div>

          <div className="space-y-1.5 text-[11px] font-medium text-slate-600">
            <div className="flex items-center gap-2">
              <span className="w-8 border-t-2 border-dashed border-blue-500" />
              Flight
            </div>

            <div className="flex items-center gap-2">
              <span className="h-1 w-8 rounded bg-blue-600" />
              Metro
            </div>

            <div className="flex items-center gap-2">
              <span className="w-8 border-t-2 border-dotted border-emerald-500" />
              Walking
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div className="absolute bottom-3 left-3 z-[1000] flex items-center gap-2 rounded-full border border-blue-100 bg-white/95 px-3 py-1.5 text-[11px] font-bold text-blue-700 shadow-md">
          <Sparkles className="h-3.5 w-3.5" />
          {status}
        </div>

        <MapContainer
          key={mapKey}
          center={
            hasLive
              ? (activeStops[0].position as [number, number])
              : [48.862, 2.337]
          }
          zoom={12}
          scrollWheelZoom
          className="h-full w-full"
        >
          <FocusActiveStop activeStopId={activeStopId} stops={activeStops} />

          <MapControls
            onLayerToggle={() => setUseLightLayer((value) => !value)}
            onStatus={setStatus}
          />

          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url={tileUrl}
          />

          <Polyline
            positions={[departureCity, destinationCity]}
            pathOptions={{
              color: "#2563eb",
              weight: 2,
              dashArray: "9, 9",
              opacity: 0.65,
            }}
          />

          <Polyline
            positions={roadRoute}
            pathOptions={{
              color: "#2563eb",
              weight: 4,
              opacity: 0.88,
              lineCap: "round",
              lineJoin: "round",
            }}
          />

          <Polyline
            positions={fallbackRoute.slice(1, 3)}
            pathOptions={{
              color: "#10b981",
              weight: 3,
              dashArray: "1, 9",
              opacity: 0.9,
            }}
          />

          {activeStops.map((stop) => (
            <Marker
              key={stop.id}
              position={stop.position}
              icon={numberIcon(stop.id, activeStopId === stop.id)}
              eventHandlers={{
                click: () => onStopFocus(stop.id),
              }}
            >
              <Popup>
                <div className="w-[230px] overflow-hidden rounded-xl bg-white">
                  <div className="h-20 bg-gradient-to-br from-blue-500 via-sky-300 to-amber-200" />

                  <div className="p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="rounded-full bg-blue-600 px-2 py-0.5 text-xs font-bold text-white">
                        Stop {stop.id}
                      </span>

                      <span className="text-xs font-semibold text-slate-500">
                        {stop.category}
                      </span>
                    </div>

                    <div className="font-bold text-slate-950">{stop.name}</div>

                    <p className="mt-1 text-xs leading-5 text-slate-600">
                      {stop.description}
                    </p>

                    <div className="mt-3 grid gap-1.5 text-xs text-slate-700">
                      <div className="flex items-center gap-2">
                        <Clock className="h-3.5 w-3.5 text-blue-600" />
                        {stop.visitTime} - {stop.duration}
                      </div>

                      <div>{stop.cost}</div>

                      {stop.transport && (
                        <div className="flex items-center gap-2">
                          <Navigation className="h-3.5 w-3.5 text-emerald-600" />
                          {stop.transport}
                        </div>
                      )}
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