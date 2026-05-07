"use client";
import React from "react";

export default function DashboardBackground() {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      {/* animated gradient */}
      <div className="absolute -top-40 -left-40 w-[800px] h-[800px] rounded-full bg-gradient-to-br from-purple-400 via-indigo-400 to-cyan-300 opacity-30 blur-3xl animate-blob" />
      <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full bg-gradient-to-tr from-pink-300 via-purple-300 to-indigo-400 opacity-25 blur-2xl animate-blob animation-delay-2000" />

      {/* subtle particles */}
      <div className="pointer-events-none absolute inset-0">
        <div className="w-full h-full bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-white/0 to-white/0 opacity-10" />
      </div>

      <style>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(20px, -30px) scale(1.05); }
          66% { transform: translate(-15px, 20px) scale(0.95); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob { animation: blob 12s ease-in-out infinite; }
        .animation-delay-2000 { animation-delay: 2s; }
      `}</style>
    </div>
  );
}
