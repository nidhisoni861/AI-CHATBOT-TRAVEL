"use client";
import React from "react";

export default function ExploreMapCard() {
  return (
    <div className="rounded-2xl bg-white/45 backdrop-blur-2xl border border-white/60 p-4 shadow-[0_20px_60px_rgba(124,58,237,0.08)] hover:-translate-y-1 transition-transform">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-500 flex items-center justify-center text-white">📍</div>
          <div className="font-semibold">Explore Map</div>
        </div>
        <div className="flex gap-2">
          <button className="w-9 h-9 rounded-full bg-white/6 hover:scale-105">+</button>
          <button className="w-9 h-9 rounded-full bg-white/6 hover:scale-105">🎯</button>
        </div>
      </div>

      <div className="relative rounded-xl overflow-hidden h-64 bg-gradient-to-br from-sky-800 to-indigo-900 text-white p-3">
        <svg viewBox="0 0 400 240" className="w-full h-full">
          <defs>
            <linearGradient id="g1" x1="0" x2="1">
              <stop offset="0%" stopColor="#7c3aed" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* land blobs */}
          <g fill="#0f172a" opacity="0.2">
            <ellipse cx="80" cy="140" rx="70" ry="30" />
            <ellipse cx="200" cy="110" rx="110" ry="40" />
            <ellipse cx="320" cy="60" rx="50" ry="25" />
          </g>

          {/* route line */}
          <path d="M80 150 C140 110 220 140 320 70" stroke="url(#g1)" strokeWidth="3" fill="none" strokeLinecap="round" filter="url(#glow)" className="animate-route-shimmer" />

          {/* glowing dots */}
          <circle cx="80" cy="150" r="5" fill="#7c3aed" className="animate-pulse-dot" />
          <circle cx="220" cy="130" r="5" fill="#06b6d4" className="animate-pulse-dot" />
          <circle cx="320" cy="70" r="5" fill="#fb7185" className="animate-pulse-dot" />

          {/* labels */}
          <text x="70" y="170" fontSize="10" fill="#c7d2fe">Paris</text>
          <text x="210" y="150" fontSize="10" fill="#c7d2fe">Barcelona</text>
          <text x="310" y="90" fontSize="10" fill="#fbcfe8">Rome</text>
        </svg>

        {/* left floating controls */}
        <div className="absolute left-3 top-3 flex flex-col gap-2">
          <button className="w-10 h-10 rounded-lg bg-white/6 hover:scale-105">↑</button>
          <button className="w-10 h-10 rounded-lg bg-white/6 hover:scale-105">⛰️</button>
          <button className="w-10 h-10 rounded-lg bg-white/6 hover:scale-105">≡</button>
        </div>

        {/* legend */}
        <div className="absolute left-3 bottom-3 bg-white/5 backdrop-blur-sm p-3 rounded-lg text-sm">
          <div className="font-semibold">Legend</div>
          <div className="flex items-center justify-between text-xs mt-2"><span>Main Route</span><span className="text-zinc-300">12.4 km</span></div>
          <div className="flex items-center justify-between text-xs mt-1"><span>Scenic Path</span><span className="text-zinc-300">8.7 km</span></div>
          <div className="flex items-center justify-between text-xs mt-1"><span>Walking Tour</span><span className="text-zinc-300">3.2 km</span></div>
        </div>
      </div>

      <div className="mt-3 flex gap-3">
        <button className="flex-1 px-4 py-2 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-500 text-white">Locate</button>
        <button className="flex-1 px-4 py-2 rounded-xl bg-white/7">Pins</button>
        <button className="flex-1 px-4 py-2 rounded-xl bg-white/7">Routes</button>
      </div>
    </div>
  );
}
