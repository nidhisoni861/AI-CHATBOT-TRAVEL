"use client";

import { useEffect, useState } from "react";
import ChatBotPanel from "@/components/Chatbot";

export default function HomePage() {
  const [showChatbot, setShowChatbot] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setShowChatbot(true);
    }, 1100);

    return () => window.clearTimeout(timer);
  }, []);

  return (
    <main className="relative h-screen overflow-hidden bg-blue-950 text-slate-950">
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/background.jpeg')",
        }}
      />

      <div className="absolute inset-0 z-[1] bg-gradient-to-br from-blue-900/40 via-blue-800/20 to-blue-950/50" />

      <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
        <div className="animate-float-slow absolute -left-16 top-10 h-72 w-72 rounded-full bg-pink-200/30 blur-3xl" />
        <div className="animate-float-medium absolute right-12 top-12 h-80 w-80 rounded-full bg-cyan-300/25 blur-3xl" />
        <div className="animate-float-reverse absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-white/20 blur-3xl" />

        <div className="absolute left-[4%] top-[8%] h-px w-[32rem] rotate-[14deg] bg-white/45" />
        <div className="absolute right-[7%] top-[14%] h-px w-[28rem] -rotate-[18deg] bg-yellow-100/35" />
        <div className="absolute bottom-[10%] right-[2%] h-px w-[38rem] -rotate-[8deg] bg-white/25" />

        <div className="absolute left-4 top-4 grid grid-cols-4 gap-4 opacity-40">
          {Array.from({ length: 28 }).map((_, index) => (
            <span
              key={index}
              className="h-1.5 w-1.5 rounded-full bg-white/70"
            />
          ))}
        </div>
      </div>

      <section className="relative z-10 flex h-screen w-full flex-col items-center px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex h-[96px] shrink-0 flex-col items-center justify-center text-center sm:h-[110px]">
          <h1 className="animate-title-reveal bg-gradient-to-r from-white via-yellow-100 to-white bg-clip-text text-4xl font-black tracking-[0.16em] text-transparent drop-shadow-[0_8px_24px_rgba(255,255,255,0.25)] sm:text-5xl lg:text-6xl">
            AI Travel Assistant Chatbot
          </h1>

          <p className="animate-subtitle-reveal mt-2 text-xs font-extrabold uppercase tracking-[0.45em] text-white/70 sm:text-sm">
            Powered by Roamora AI
          </p>
        </div>

        <div
          className={`flex min-h-0 w-full flex-1 items-center justify-center transition-all duration-700 ${
            showChatbot
              ? "translate-y-0 opacity-100"
              : "translate-y-8 opacity-0"
          }`}
        >
          {showChatbot && <ChatBotPanel />}
        </div>
      </section>
    </main>
  );
}