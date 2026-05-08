"use client";
import React from "react";

export default function DashboardHeader() {
  return (
    <div className="w-full rounded-[28px] bg-white/55 backdrop-blur-xl border border-white/40 shadow-[0_20px_60px_rgba(99,102,241,0.16)] px-6 py-4 flex items-center justify-between h-24">
      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-600 via-fuchsia-500 to-sky-500 flex items-center justify-center text-white font-bold shadow-lg">WA</div>
        <div>
          <div className="text-xl font-semibold">WanderAI</div>
          <div className="text-xs text-slate-500">AI Travel Assistant</div>
        </div>
      </div>

      <div className="text-center max-w-2xl px-6">
        <div className="flex items-center justify-center gap-3">
          <div className="text-sm text-slate-600">Your intelligent travel companion, anywhere in the world.</div>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-100 to-white flex items-center justify-center text-indigo-600 shadow-sm">🔊</div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button aria-label="settings" className="p-2 rounded-full bg-white/6 border border-white/6 shadow-sm">⚙️</button>
        <div className="relative">
          <button aria-label="notifications" className="p-2 rounded-full bg-white/6 border border-white/6 shadow-sm">🔔</button>
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-pink-400 rounded-full ring-2 ring-white"></span>
        </div>
        <div className="flex items-center gap-3 px-4 py-2 rounded-full bg-gradient-to-br from-indigo-500 to-pink-400 text-white shadow-md">
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-xs font-semibold">T</div>
          <div className="text-sm">Traveler</div>
        </div>
      </div>
    </div>
  );
}
