"use client";
import React from "react";

export default function ExploreMapCard() {
  return (
    <div className="rounded-2xl bg-white/60 dark:bg-zinc-900/60 backdrop-blur-md border border-white/6 p-4 shadow-2xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold">Explore Map</h3>
        <div className="flex gap-2">
          <button className="w-8 h-8 rounded-full bg-white/8 hover:bg-white/10 flex items-center justify-center">+</button>
          <button className="w-8 h-8 rounded-full bg-white/8 hover:bg-white/10 flex items-center justify-center">−</button>
          <button className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-white">📍</button>
        </div>
      </div>

      <div className="relative w-full h-64 rounded-xl overflow-hidden bg-gradient-to-br from-cyan-50 to-indigo-50 dark:from-black/20 dark:to-zinc-900">
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 240" preserveAspectRatio="none">
          <defs>
            <linearGradient id="route" x1="0" x2="1">
              <stop offset="0%" stopColor="#7c3aed" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
          </defs>
          <path d="M20,200 C100,120 200,180 380,40" stroke="url(#route)" strokeWidth="4" fill="none" opacity="0.95" strokeLinecap="round" />
          <circle cx="60" cy="170" r="6" fill="#7c3aed" />
          <circle cx="220" cy="120" r="6" fill="#06b6d4" />
          <circle cx="360" cy="40" r="6" fill="#fb7185" />
        </svg>

        {/* floating pins */}
        <div className="absolute left-8 top-10 bg-white/80 rounded-full p-1 shadow-md">📍</div>
        <div className="absolute right-10 bottom-14 bg-white/80 rounded-full p-1 shadow-md">📍</div>

        {/* soft grid dots */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(255,255,255,0.06),transparent)] pointer-events-none" />
      </div>

      <div className="mt-3 bg-white/5 rounded-xl p-3 grid gap-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gradient-to-r from-indigo-600 to-cyan-400" />
            <span>Main Route</span>
          </div>
          <div className="text-xs text-zinc-400">12.4 km</div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gradient-to-r from-pink-400 to-rose-400" />
            <span>Scenic Path</span>
          </div>
          <div className="text-xs text-zinc-400">8.7 km</div>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-300" />
            <span>Walking Tour</span>
          </div>
          <div className="text-xs text-zinc-400">3.2 km</div>
        </div>
      </div>
    </div>
  );
}
