"use client";
import React from "react";

export default function DashboardBackground() {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
      <div className="absolute -left-72 -top-56 w-[900px] h-[900px] rounded-full bg-gradient-to-br from-[#c4b5fd] via-[#a78bfa] to-[#7dd3fc] opacity-30 blur-3xl animate-float-slow" />
      <div className="absolute -right-72 -bottom-56 w-[700px] h-[700px] rounded-full bg-gradient-to-tr from-[#fbcfe8] via-[#f0abfc] to-[#60a5fa] opacity-20 blur-2xl animate-float-medium" />

      {/* light streaks */}
      <div className="absolute left-1/2 top-10 w-[1200px] h-[80px] -translate-x-1/2 bg-[linear-gradient(90deg,rgba(255,255,255,0.02),rgba(255,255,255,0.06),rgba(255,255,255,0.02))] opacity-20 blur-xl animate-light-streak" />

      {/* particles */}
      <div className="absolute inset-0">
        <div className="w-full h-full">
          {[...Array(24)].map((_, i) => (
            <div
              key={i}
              className={`absolute bg-white/40 rounded-full opacity-20`} 
              style={{
                width: `${6 + (i % 5)}px`,
                height: `${6 + (i % 5)}px`,
                left: `${(i * 37) % 100}%`,
                top: `${(i * 53) % 100}%`,
                transform: `translate(-50%, -50%)`,
                animation: `particleDrift ${8 + (i % 6)}s ease-in-out ${i % 3}s infinite alternate`,
              }}
            />
          ))}
        </div>
      </div>

      <style>{`
        @keyframes floatSlow { 0% { transform: translateY(0px) } 50% { transform: translateY(-20px) } 100% { transform: translateY(0px) } }
        @keyframes floatMedium { 0% { transform: translateY(0px) } 50% { transform: translateY(-10px) } 100% { transform: translateY(0px) } }
        @keyframes light-streak { 0% { transform: translateX(-10%) } 50% { transform: translateX(10%) } 100% { transform: translateX(-10%) } }
        @keyframes particleDrift { 0% { transform: translateY(0px) } 100% { transform: translateY(-30px) } }
        .animate-float-slow { animation: floatSlow 14s ease-in-out infinite; }
        .animate-float-medium { animation: floatMedium 10s ease-in-out infinite; }
        .animate-light-streak { animation: light-streak 18s linear infinite; }
      `}</style>
    </div>
  );
}
