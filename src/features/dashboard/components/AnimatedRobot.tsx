"use client";
import React from "react";

export default function AnimatedRobot() {
  return (
    <div className="relative flex items-center justify-center">
      <div className="w-44 h-44 rounded-full bg-gradient-to-br from-white to-slate-100 flex items-center justify-center shadow-2xl relative">
        <div className="absolute inset-0 rounded-full ring-4 ring-violet-300/30 animate-pulse-slow" />
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-slate-900 to-slate-700 flex items-center justify-center text-white shadow-inner">
          <div className="w-10 h-6 bg-[#0ea5b7] rounded-full flex items-center justify-center">• •</div>
        </div>
      </div>

      {/* hologram rings */}
      <div className="absolute w-56 h-56 rounded-full border border-violet-200/20 blur-sm animate-orbit" />
      <div className="absolute w-72 h-72 rounded-full border border-cyan-200/10 blur-lg animate-orbit animation-delay-2000" />
    </div>
  );
}
