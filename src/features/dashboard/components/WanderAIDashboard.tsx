"use client";
import React from "react";
import DashboardBackground from "@/src/features/dashboard/components/DashboardBackground";
import DashboardHeader from "@/src/features/dashboard/components/DashboardHeader";
import ExploreMapCard from "@/src/features/dashboard/components/ExploreMapCard";
import AiAssistantCard from "@/src/features/dashboard/components/AiAssistantCard";
import SavedTripsCard from "@/src/features/dashboard/components/SavedTripsCard";

export function WanderAIDashboard() {
  return (
    <div className="min-h-screen relative bg-[linear-gradient(180deg,#eef2ff_0%,#fff1f8_100%)]">
      <DashboardBackground />
      <div className="max-w-[1500px] mx-auto px-6 py-6 relative z-10">
        <DashboardHeader />

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[1fr_1.08fr_1fr] gap-6 items-start">
          <div className="lg:col-span-1">
            <ExploreMapCard />
          </div>
          <div className="lg:col-span-1 md:col-span-2">
            <AiAssistantCard />
          </div>
          <div className="lg:col-span-1">
            <SavedTripsCard />
          </div>
        </div>
      </div>
    </div>
  );
}

export default WanderAIDashboard;
