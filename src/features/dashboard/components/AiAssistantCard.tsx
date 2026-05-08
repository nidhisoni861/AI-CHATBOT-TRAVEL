"use client";
import React from "react";
import AnimatedRobot from "@/src/features/dashboard/components/AnimatedRobot";

export default function AiAssistantCard() {
  return (
    <div className="rounded-3xl bg-white/50 backdrop-blur-2xl border border-white/60 p-6 shadow-[0_30px_100px_rgba(99,102,241,0.12)] hover:-translate-y-1 transition-transform">
      <div className="flex flex-col items-center">
        <AnimatedRobot />
        <h2 className="mt-4 text-3xl font-semibold">Hello, Traveler! <span className="text-2xl">👋</span></h2>
        <p className="text-sm text-slate-600 mt-2">How can I help you plan your next adventure?</p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        {[
          { title: "Plan a trip", subtitle: "Personalized itineraries", emoji: "🧭" },
          { title: "Find stays", subtitle: "Hotels & unique stays", emoji: "🏨" },
          { title: "Explore attractions", subtitle: "Top sights & hidden gems", emoji: "🏛️" },
          { title: "Check travel tips", subtitle: "Smart tips & safety", emoji: "📝" },
        ].map((a) => (
          <button key={a.title} className="p-4 rounded-xl bg-white/5 backdrop-blur-sm hover:scale-105 transition-transform flex items-start gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-violet-600 to-sky-500 flex items-center justify-center text-white text-xl">{a.emoji}</div>
            <div className="text-left">
              <div className="text-sm font-medium">{a.title}</div>
              <div className="text-xs text-slate-500">{a.subtitle}</div>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-6">
        <div className="rounded-2xl p-4 bg-gradient-to-r from-indigo-50 to-sky-50 text-slate-700">I can help you discover amazing places, plan itineraries, find stays, and much more. What are you thinking about?</div>
        <div className="ml-auto max-w-[70%] mt-3 rounded-2xl p-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">Suggest a 4-day trip in Europe</div>
      </div>

      <div className="mt-6">
        <div className="flex items-center gap-3 bg-white/5 border border-white/6 rounded-full px-3 py-2">
          <button className="p-2 rounded-full bg-white/6">+</button>
          <input className="flex-1 bg-transparent outline-none text-sm" placeholder="Ask anything about your trip..." />
          <button className="p-2">🎤</button>
          <button className="px-4 py-2 rounded-full bg-gradient-to-br from-violet-600 to-sky-500 text-white hover:scale-105 transition-transform">Send</button>
        </div>
        <div className="text-xs text-slate-500 mt-2">WanderAI can make mistakes. Please verify important information.</div>
      </div>
    </div>
  );
}
