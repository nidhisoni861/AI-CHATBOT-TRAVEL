"use client";
import React from "react";

export default function DashboardHeader() {
  return (
    <header className="flex items-center justify-between py-4 px-6 bg-transparent">
      <div className="flex items-center gap-3">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-600 to-purple-500 flex items-center justify-center shadow-lg border border-white/10">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="6" fill="white" opacity="0.06" />
            <path d="M7 12a5 5 0 0 0 10 0" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.9" />
          </svg>
        </div>
        <div>
          <div className="text-lg font-semibold">WanderAI</div>
          <div className="text-xs text-zinc-400">AI Travel Assistant</div>
        </div>
      </div>

      <div className="text-center max-w-lg">
        <div className="text-sm text-zinc-600 dark:text-zinc-300">Your intelligent travel companion, anywhere in the world.</div>
      </div>

      <div className="flex items-center gap-3">
        <button className="p-2 rounded-full bg-white/5 hover:bg-white/7 border border-white/6 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-zinc-200" viewBox="0 0 24 24" fill="none">
            <path stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" d="M12 3v3M12 18v3M4.2 6.2l2 2M17.8 17.8l2 2M3 12h3M18 12h3M4.2 17.8l2-2M17.8 6.2l2-2" />
          </svg>
        </button>
        <button className="p-2 rounded-full bg-white/5 hover:bg-white/7 border border-white/6 shadow-sm">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5 text-zinc-200" viewBox="0 0 24 24" fill="none">
            <path stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0 1 18 14.158V11a6 6 0 0 0-5-5.917V4a2 2 0 1 0-4 0v1.083A6 6 0 0 0 4 11v3.159c0 .538-.214 1.055-.595 1.436L2 17h5" />
          </svg>
        </button>
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/6 shadow-sm">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-pink-400 flex items-center justify-center text-xs font-semibold text-white">T</div>
          <div className="text-sm">Traveler</div>
        </div>
      </div>
    </header>
  );
}
