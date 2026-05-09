"use client";

import { useEffect } from "react";
import L, { type LatLngBoundsExpression, type LatLngExpression } from "leaflet";
import {
  MapContainer,
  Marker,
  Polyline,
  Popup,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";

type RoutePoint = {
  id: number;
  city: string;
  days: string;
  position: [number, number];
};

const routePoints: RoutePoint[] = [
  {
    id: 1,
    city: "Rome",
    days: "Days 1-2",
    position: [41.9028, 12.4964],
  },
  {
    id: 2,
    city: "Florence",
    days: "Days 3-4",
    position: [43.7696, 11.2558],
  },
  {
    id: 3,
    city: "Amalfi Coast",
    days: "Days 5-7",
    position: [40.634, 14.6027],
  },
];

const routePositions: LatLngExpression[] = routePoints.map(
  (point) => point.position
);

function createNumberIcon(number: number) {
  return L.divIcon({
    className: "custom-route-marker",
    html: `
      <div style="
        width: 38px;
        height: 38px;
        border-radius: 9999px;
        background: linear-gradient(135deg, #008f95, #14b8a6);
        color: white;
        border: 4px solid white;
        box-shadow: 0 10px 28px rgba(0, 143, 149, 0.42);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        font-weight: 900;
        font-family: Arial, Helvetica, sans-serif;
      ">
        ${number}
      </div>
    `,
    iconSize: [38, 38],
    iconAnchor: [19, 19],
    popupAnchor: [0, -20],
  });
}

function FitMapToItalyRoute() {
  const map = useMap();

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      map.invalidateSize();

      const bounds = routePoints.map((point) => point.position);

      map.fitBounds(bounds as LatLngBoundsExpression, {
        padding: [38, 38],
        maxZoom: 6,
      });
    }, 250);

    return () => window.clearTimeout(timeout);
  }, [map]);

  return null;
}

export default function ItalyLeafletMap() {
  return (
    <MapContainer
      center={[42.25, 12.8]}
      zoom={6}
      minZoom={5}
      maxZoom={11}
      scrollWheelZoom={false}
      zoomControl={false}
      attributionControl={false}
      className="h-full w-full rounded-[22px]"
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      <Polyline
        positions={routePositions}
        pathOptions={{
          color: "#008f95",
          weight: 4,
          opacity: 0.9,
          dashArray: "9 9",
          lineCap: "round",
          lineJoin: "round",
        }}
      />

      {routePoints.map((point) => (
        <Marker
          key={point.id}
          position={point.position}
          icon={createNumberIcon(point.id)}
        >
          <Popup>
            <div className="text-sm">
              <strong>{point.city}</strong>
              <br />
              {point.days}
            </div>
          </Popup>

          <Tooltip
            permanent
            direction="right"
            offset={[16, 0]}
            className="route-city-tooltip"
          >
            <div>
              <strong>{point.city}</strong>
              <br />
              <span>{point.days}</span>
            </div>
          </Tooltip>
        </Marker>
      ))}

      <FitMapToItalyRoute />
    </MapContainer>
  );
}