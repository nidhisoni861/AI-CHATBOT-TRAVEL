"use client";
import React from "react";

export function TravelDashboard() {
  return (
    <div className="min-h-screen bg-white p-6 text-zinc-900">
      <header className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white font-bold">WA</div>
          <div>
            <div className="text-lg font-semibold">WanderAI</div>
            <div className="text-xs text-zinc-500">AI Travel Assistant</div>
          </div>
        </div>

        <div className="text-center max-w-md">
          <div className="text-sm text-zinc-600">Your intelligent travel companion, anywhere in the world.</div>
        </div>

        <div className="flex items-center gap-3">
          <button className="p-2 rounded-md hover:bg-zinc-100">⚙️</button>
          <button className="p-2 rounded-md hover:bg-zinc-100">🔔</button>
          <div className="flex items-center gap-2 p-2 rounded-md bg-zinc-100">
            <div className="w-6 h-6 rounded-full bg-zinc-300" />
            <div className="text-sm">Traveler</div>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="space-y-4">
          <div className="rounded-2xl bg-gradient-to-b from-white to-zinc-50 shadow-md p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold">Explore Map</h3>
              <div className="flex items-center gap-2">
                <button className="p-1 rounded-md bg-white shadow-sm">+</button>
                <button className="p-1 rounded-md bg-white shadow-sm">-</button>
              </div>
            </div>

            <div className="relative h-64 rounded-xl overflow-hidden bg-gradient-to-br from-sky-50 to-indigo-50">
              {/* stylized map placeholder */}
              <div className="absolute inset-4 rounded-lg bg-gradient-to-br from-indigo-100 to-sky-50 opacity-60" />
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 200" preserveAspectRatio="none">
                <path d="M20 160 C80 120 120 40 200 60 C280 80 320 140 380 120" stroke="#7c3aed" strokeWidth="3" fill="none" strokeOpacity="0.6" />
                <circle cx="40" cy="150" r="4" fill="#7c3aed" />
                <circle cx="200" cy="60" r="5" fill="#06b6d4" />
                <circle cx="360" cy="110" r="4" fill="#a78bfa" />
              </svg>

              <div className="absolute bottom-4 left-4 bg-white/80 px-3 py-2 rounded-lg shadow-sm text-xs">
                <div className="font-medium">Legend</div>
                <div className="mt-1 text-zinc-600 text-[12px]">
                  <div>Main Route — 12.4 km</div>
                  <div>Scenic Path — 8.7 km</div>
                  <div>Walking Tour — 3.2 km</div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-white shadow-md p-4">
            <h4 className="text-sm font-semibold mb-2">Map Controls</h4>
            <div className="flex gap-2">
              <button className="px-3 py-2 rounded-md bg-indigo-600 text-white">Locate</button>
              <button className="px-3 py-2 rounded-md border">Pins</button>
              <button className="px-3 py-2 rounded-md border">Routes</button>
            </div>
          </div>
        </div>

        {/* Center column */}
        <div className="col-span-1 lg:col-span-1">
          <div className="rounded-3xl bg-white shadow-lg p-6">
            <div className="flex flex-col items-center gap-3 mb-4">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-white text-2xl">🤖</div>
              <h2 className="text-xl font-semibold">Hello, Traveler! 👋</h2>
              <p className="text-sm text-zinc-600 text-center">How can I help you plan your next adventure?</p>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              <button className="p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50 hover:shadow-md">Plan a trip</button>
              <button className="p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50 hover:shadow-md">Find stays</button>
              <button className="p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50 hover:shadow-md">Explore attractions</button>
              <button className="p-4 rounded-2xl bg-gradient-to-br from-purple-50 to-indigo-50 hover:shadow-md">Check travel tips</button>
            </div>

            <div className="space-y-3 mb-4">
              <div className="rounded-2xl bg-zinc-100 p-3 max-w-[80%]">I can help you discover amazing places, plan itineraries, find stays, and much more. What are you thinking about?</div>
              <div className="rounded-2xl bg-indigo-600 text-white p-3 max-w-[65%] ml-auto">Suggest a 4-day trip in Europe</div>
            </div>

            <div className="mt-4">
              <div className="rounded-full border px-3 py-2 flex items-center gap-2">
                <button className="p-2 rounded-full">+</button>
                <input className="flex-1 outline-none text-sm" placeholder="Ask anything about your trip..." />
                <button className="p-2">🎤</button>
                <button className="p-2 rounded-full bg-indigo-600 text-white">Send</button>
              </div>
              <div className="text-[11px] text-zinc-400 mt-2">WanderAI can make mistakes. Please verify important information.</div>
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          <div className="rounded-2xl bg-white shadow-md p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold">Saved Trips</h3>
              <button className="text-xs px-2 py-1 rounded bg-indigo-600 text-white">New Trip</button>
            </div>

            <div className="space-y-3">
              {[
                { title: "Paris Getaway", date: "Jun 12 – Jun 16, 2025", days: 4, people: 2, badge: "Upcoming" },
                { title: "Tokyo Explorer", date: "Jul 03 – Jul 10, 2025", days: 7, people: 1, badge: "Upcoming" },
                { title: "Barcelona Escape", date: "May 20 – May 24, 2025", days: 5, people: 2, badge: "Completed" },
                { title: "Bali Retreat", date: "Aug 15 – Aug 22, 2025", days: 8, people: 2, badge: "Saved" },
              ].map((t) => (
                <div key={t.title} className="flex items-center justify-between p-3 rounded-xl border">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-300 to-purple-300" />
                    <div>
                      <div className="font-medium">{t.title}</div>
                      <div className="text-xs text-zinc-500">{t.date}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-xs text-zinc-500">{t.days}d • {t.people}p</div>
                    <div className="text-xs px-2 py-1 rounded-full bg-zinc-100">{t.badge}</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4">
              <button className="w-full px-3 py-2 rounded-md bg-white border">View All Trips</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TravelDashboard;
