"use client";
import React from "react";
import DashboardBackground from "@/src/features/chatbot/components/DashboardBackground";
import DashboardHeader from "@/src/features/chatbot/components/DashboardHeader";
import ExploreMapCard from "@/src/features/chatbot/components/ExploreMapCard";
import AiAssistantCard from "@/src/features/chatbot/components/AiAssistantCard";
import SavedTripsCard from "@/src/features/chatbot/components/SavedTripsCard";

export function TravelDashboard() {
  return (
    <div className="min-h-screen relative overflow-hidden bg-neutral-50">
      <DashboardBackground />
      <div className="max-w-7xl mx-auto px-4 py-6">
        <DashboardHeader />

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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

export default TravelDashboard;
