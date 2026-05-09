"use client";

import dynamic from "next/dynamic";
import {
  ArrowRight,
  CalendarDays,
  Map,
  Maximize2,
  MoreHorizontal,
  Users,
} from "lucide-react";

const ItalyLeafletMap = dynamic(() => import("./ItalyLeafletMap"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center rounded-[22px] bg-cyan-50 text-sm font-bold text-teal-700">
      Loading Italy map...
    </div>
  ),
});

export default function RouteCard() {
  return (
    <aside className="w-full rounded-[28px] border border-white/70 bg-white/80 p-4 shadow-[0_24px_70px_rgba(15,23,42,0.20)] backdrop-blur-2xl">
      <header className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Map className="h-5 w-5 text-slate-800" />
          <h2 className="text-base font-extrabold tracking-tight text-slate-950 2xl:text-lg">
            Italy Route
          </h2>
        </div>

        <button
          aria-label="More route options"
          className="rounded-full p-2 text-slate-600 transition hover:bg-white/80"
        >
          <MoreHorizontal className="h-5 w-5" />
        </button>
      </header>

      <div className="relative h-[255px] overflow-hidden rounded-[22px] border border-white/80 bg-cyan-50 shadow-inner 2xl:h-[285px]">
        <ItalyLeafletMap />

        <button
          aria-label="Expand map"
          className="absolute bottom-3 right-3 z-[500] flex h-10 w-10 items-center justify-center rounded-full bg-white/95 text-slate-700 shadow-lg backdrop-blur transition hover:scale-105"
        >
          <Maximize2 className="h-4 w-4" />
        </button>
      </div>

      <section className="mt-4">
        <h3 className="text-lg font-extrabold tracking-tight text-slate-950 2xl:text-xl">
          7-day Italy Escape
        </h3>

        <div className="mt-3 space-y-2.5">
          <div className="flex items-center gap-3 text-sm font-semibold text-slate-700">
            <CalendarDays className="h-[18px] w-[18px] text-slate-800" />
            <span>Jun 10 – Jun 16, 2025</span>
          </div>

          <div className="flex items-center gap-3 text-sm font-semibold text-slate-700">
            <Users className="h-[18px] w-[18px] text-slate-800" />
            <span>2 Travelers</span>
          </div>
        </div>

        <button className="mt-4 flex w-full items-center justify-between rounded-2xl bg-white/75 px-4 py-3.5 text-left text-sm font-extrabold text-teal-700 transition hover:bg-teal-50 hover:text-teal-800">
          <span>View full itinerary</span>
          <ArrowRight className="h-5 w-5 text-slate-800" />
        </button>
      </section>
    </aside>
  );
}