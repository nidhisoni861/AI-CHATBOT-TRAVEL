"use client";

import { useRef, useState } from "react";

import { LeftSidebar } from "../../../components/layout/LeftSidebar";
import { PremiumMap } from "../../maps/components/PremiumMap";
import { FloatingAssistant } from "../../travel/components/FloatingAssistant";
import { LiveTranslation } from "../../translator/components/LiveTranslation";

import {
  dashboardCopyByLanguage,
  defaultDashboardCopy,
  initialBookingPrices,
  optimizedBookingPrices,
} from "../data/dashboard-copy";

import type { SupportedLanguage } from "../types/dashboard.types";

import { RefinedItinerary } from "../../travel/components/RefinedItinerary";
import {
  SavedTripsWidget,
  type SavedTrip,
} from "../../travel/components/SavedTripsWidget";
import { TravelInsights } from "../../travel/components/TravelInsights";
// import { TravelOperations } from "../../travel/components/TravelOperations";

import type { DashboardPayload } from "../../../lib/api";
import { normalizeItinerary } from "../../../lib/api";

const LIVE_TINTS = [
  "from-violet-500 to-fuchsia-400",
  "from-cyan-500 to-blue-400",
  "from-amber-500 to-orange-400",
  "from-rose-500 to-pink-400",
  "from-emerald-500 to-teal-400",
];

export default function DashboardView() {
  const [activeSection, setActiveSection] = useState("overview");
  const [assistantOpen, setAssistantOpen] = useState(true);
  const [pageLanguage, setPageLanguage] =
    useState<SupportedLanguage>("English");

  const [activeStopId, setActiveStopId] = useState(1);
  const [, setBudget] = useState(1500);
  const [bookingPrices, setBookingPrices] = useState(initialBookingPrices);
  const [liveTripData, setLiveTripData] = useState<DashboardPayload | null>(
    null
  );
  const [liveTrips, setLiveTrips] = useState<SavedTrip[]>([]);

  const overviewRef = useRef<HTMLDivElement>(null);
  const tripPlannerRef = useRef<HTMLDivElement>(null);
  const mapRouteRef = useRef<HTMLDivElement>(null);
  const translationRef = useRef<HTMLDivElement>(null);
  const savedTripsRef = useRef<HTMLDivElement>(null);

  const sectionRefs = {
    overview: overviewRef,
    "trip-planner": tripPlannerRef,
    "map-route": mapRouteRef,
    translation: translationRef,
    "saved-trips": savedTripsRef,
  };

  const handleDashboardUpdate = (payload: DashboardPayload) => {
    const normalized = {
      ...payload,
      itinerary: normalizeItinerary(payload.itinerary),
    };

    setLiveTripData(normalized);

    const budgetTotal = normalized.budget_breakdown?.total;

    if (typeof budgetTotal === "number" && budgetTotal > 0) {
      setBudget(budgetTotal);
    }

    const summary = normalized.trip_summary as
      | Record<string, unknown>
      | undefined;

    const destination =
      (summary?.destination as string) ||
      (summary?.city as string) ||
      (summary?.title as string) ||
      "";

    const days =
      normalized.itinerary.length > 0
        ? `${Math.max(...normalized.itinerary.map((stop) => stop.day))} days`
        : "";

    const budgetText = budgetTotal
      ? `${normalized.budget_breakdown?.currency ?? "EUR"} ${budgetTotal}`
      : "";

    if (!destination) return;

    const newTrip: SavedTrip = {
      destination,
      dates: "AI Generated",
      status: "AI",
      budget: budgetText,
      days,
      tint: LIVE_TINTS[liveTrips.length % LIVE_TINTS.length],
      isLive: true,
    };

    setLiveTrips((prev) => {
      const alreadyExists = prev.some(
        (trip) => trip.destination === destination
      );

      if (alreadyExists) {
        return prev.map((trip) =>
          trip.destination === destination
            ? { ...trip, budget: budgetText, days }
            : trip
        );
      }

      return [newTrip, ...prev];
    });
  };

  const copy = dashboardCopyByLanguage[pageLanguage] ?? defaultDashboardCopy;

  const handleSectionChange = (section: string) => {
    setActiveSection(section);

    sectionRefs[section as keyof typeof sectionRefs]?.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const handleLanguageChange = (language: string) => {
    if (language in dashboardCopyByLanguage) {
      setPageLanguage(language as SupportedLanguage);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#eef3fb] text-slate-950 lg:flex-row">
      {/* <LeftSidebar
        activeSection={activeSection}
        onSectionChange={handleSectionChange}
        pageLanguage={pageLanguage}
        onLanguageChange={handleLanguageChange}
      /> */}

      <main className="flex-1 overflow-y-auto lg:h-screen">
        <div className="mx-auto w-full max-w-[1840px] px-6 py-6 2xl:px-8">
          {/* HEADER */}
          <section ref={overviewRef} className="scroll-mt-6">
            <div className="mx-auto mb-8 flex max-w-4xl flex-col items-center justify-center text-center">
              <div className="mb-3 inline-flex items-center justify-center gap-2 rounded-full border border-blue-200 bg-white/80 px-4 py-2 text-xs font-bold uppercase tracking-[0.22em] text-blue-700 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_14px_rgba(52,211,153,.85)]" />
                {copy.eyebrow}
              </div>

              <h1 className="mx-auto max-w-4xl text-center text-3xl font-extrabold tracking-tight text-slate-950 sm:text-4xl lg:text-5xl">
                {copy.title}
              </h1>

              <p className="mx-auto mt-4 max-w-2xl text-center text-sm leading-7 text-slate-600 sm:text-base">
                {copy.body}
              </p>
            </div>
          </section>

          {/* CLEAN 3-COLUMN GRID */}
          <section
            ref={tripPlannerRef}
            className="grid scroll-mt-6 items-start gap-6 xl:grid-cols-[minmax(330px,0.95fr)_minmax(470px,1.18fr)_minmax(360px,0.95fr)]"
          >
            {/* LEFT COLUMN */}

            <div className="min-w-0 space-y-6">
              <div ref={translationRef} className="scroll-mt-6">
                {/* <LiveTranslation /> */}
              </div>  
              <div ref={mapRouteRef} className="scroll-mt-6">
                <PremiumMap
                  activeStopId={activeStopId}
                  onStopFocus={setActiveStopId}
                  liveStops={liveTripData?.itinerary}
                />
              </div>

              {/* <TravelOperations bookingPrices={bookingPrices} /> */}

              
            </div>

            {/* CENTER COLUMN */}
            <div className="min-w-0 space-y-6">
              <FloatingAssistant
                docked
                isOpen={assistantOpen}
                onToggle={() => setAssistantOpen((prev) => !prev)}
                onSetBudget={setBudget}
                onOptimizePrices={() => setBookingPrices(optimizedBookingPrices)}
                onFocusStop={setActiveStopId}
                onDashboardUpdate={handleDashboardUpdate}
              />
             


              
              
            </div>

            {/* RIGHT COLUMN - ONLY STICKY ASSISTANT */}
            <div className=" h-50 min-w-5 space-y-6 scroll-mt-6">
               {/* <RefinedItinerary
                activeStopId={activeStopId}
                onStopChange={setActiveStopId}
                liveStops={liveTripData?.itinerary}
                tripSummary={liveTripData?.trip_summary}
              /> */}
              <div ref={savedTripsRef} className="scroll-mt-6">
                <SavedTripsWidget liveTrips={liveTrips} />
              </div>
              {/* <TravelInsights /> */}
              
            </div>
            
          </section>
          
        </div>
      </main>
    </div>
  );
}