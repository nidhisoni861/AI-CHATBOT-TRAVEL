"use client";
import React from "react";

export default function AiAssistantCard() {
  return (
    <div className="rounded-3xl bg-white/60 dark:bg-zinc-900/60 backdrop-blur-md border border-white/6 p-6 shadow-2xl flex flex-col">
      <div className="flex flex-col items-center">
        <div className="w-28 h-28 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center shadow-xl relative">
          <div className="absolute inset-0 rounded-full ring-4 ring-indigo-300/20 animate-pulse" />
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
            <path d="M12 2a5 5 0 100 10 5 5 0 000-10z" fill="#fff" opacity="0.08" />
            <path d="M8 12c1.333 1.333 3.333 2 6 2s4-0.667 5-2" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>

        <h2 className="mt-4 text-2xl font-semibold">Hello, Traveler! <span className="text-xl">👋</span></h2>
        <p className="text-sm text-zinc-500 mt-2">How can I help you plan your next adventure?</p>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        {[
          { title: "Plan a trip", emoji: "🧭" },
          { title: "Find stays", emoji: "🏨" },
          { title: "Explore attractions", emoji: "🏛️" },
          { title: "Check travel tips", emoji: "📝" },
        ].map((q) => (
          <button key={q.title} className="flex items-center gap-3 p-4 rounded-xl bg-white/5 hover:scale-[1.02] transition-transform shadow-sm">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-500 flex items-center justify-center text-white text-lg">{q.emoji}</div>
            <div className="text-left">
              <div className="text-sm font-medium">{q.title}</div>
              <div className="text-xs text-zinc-400">Quick action</div>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-6 flex-1 overflow-auto">
        <div className="max-w-2xl mx-auto flex flex-col gap-4">
          <div className="rounded-2xl p-4 bg-indigo-50 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50 shadow-sm">
            I can help you discover amazing places, plan itineraries, find stays, and much more. What are you thinking about?
          </div>

          <div className="ml-auto max-w-[70%] rounded-2xl p-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm">
            Suggest a 4-day trip in Europe
          </div>
        </div>
      </div>

      <div className="mt-6">
        <div className="flex items-center gap-3 bg-white/5 border border-white/6 rounded-full px-3 py-2">
          <button className="p-2 rounded-full bg-white/6">+</button>
          <input className="flex-1 bg-transparent outline-none text-sm" placeholder="Ask anything about your trip..." />
          <button className="p-2">🎤</button>
          <button className="px-4 py-2 rounded-full bg-gradient-to-r from-indigo-600 to-purple-500 text-white hover:scale-105 transition-transform">Send</button>
        </div>
        <div className="text-xs text-zinc-400 mt-2">WanderAI can make mistakes. Please verify important information.</div>
      </div>
    </div>
  );
}
