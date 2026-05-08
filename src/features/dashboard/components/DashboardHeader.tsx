"use client";
import React from "react";

export default function DashboardHeader() {
  return (
    <div className="w-full rounded-[28px] bg-white/45 backdrop-blur-xl border border-white/50 shadow-[0_20px_60px_rgba(99,102,241,0.18)] px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 via-fuchsia-500 to-sky-500 flex items-center justify-center text-white font-bold shadow-md">WA</div>
        <div>
          <div className="text-lg font-semibold">WanderAI</div>
          <div className="text-xs text-slate-600">AI Travel Assistant</div>
        </div>
      </div>

      <div className="text-center max-w-xl">
        <div className="text-sm text-slate-600">Your intelligent travel companion, anywhere in the world.</div>
      </div>

      <div className="flex items-center gap-3">
        <button className="p-2 rounded-full bg-white/5 border border-white/6">⚙️</button>
        <div className="relative">
          <button className="p-2 rounded-full bg-white/5 border border-white/6">🔔</button>
          <span className="absolute -top-1 -right-1 w-2 h-2 bg-pink-400 rounded-full ring-2 ring-white"></span>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-br from-indigo-500 to-pink-400 text-white">
          <div className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center text-xs">T</div>
          <div className="text-sm">Traveler</div>
        </div>
      </div>
    </div>
  );
}
