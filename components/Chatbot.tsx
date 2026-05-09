"use client";
import { useState } from "react";

const suggestions = [
  { icon: "📅", text: "1 Day trip to Berlin" },
  { icon: "📅", text: "3 day trip to Munich with faster pace" },
  { icon: "🍴", text: "5 day trip to Stuttgart with more food experiences" },
];

function MicIcon({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="9" y1="22" x2="15" y2="22" />
    </svg>
  );
}

function SendIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
    </svg>
  );
}

export default function Chatbot() {
  const [voice, setVoice] = useState(true);
  const [input, setInput] = useState("");

  return (
    <div
      className="h-screen overflow-hidden flex flex-col items-center gap-3 px-4 py-4 sm:px-6 sm:py-5"
      style={{ background: "linear-gradient(135deg, #0d9488 0%, #2dd4bf 28%, #f9a8d4 62%, #fb923c 100%)" }}
    >
      <div className="w-full flex flex-col items-center gap-3 h-full">
      {/* Project Title */}
      <div className="text-center flex-shrink-0">
        <h1
          className="title-gradient font-black tracking-tight leading-none"
          style={{
            fontSize: "clamp(1.8rem, 5vw, 3.8rem)",
            filter: "drop-shadow(0 2px 16px rgba(255,255,255,0.3))",
          }}
        >
          AI Travel Assistant Chatbot
        </h1>
        <p
          className="subtitle-animate mt-1 text-xs sm:text-sm font-semibold tracking-widest uppercase"
          style={{ color: "rgba(255,255,255,0.5)" }}
        >
          Powered by Roamora AI
        </p>
      </div>

      {/* White Chatbot Card — fills remaining height */}
      <div className="card-animate backdrop-blur-2xl rounded-2xl sm:rounded-3xl p-5 sm:p-8 w-full max-w-6xl flex flex-col gap-4 flex-1 overflow-hidden"
        style={{
          background: "rgba(255, 255, 255, 0.68)",
          border: "1px solid rgba(255, 255, 255, 0.8)",
          boxShadow: "0 8px 40px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.9)",
        }}>

        {/* Header */}
        <div className="flex items-center justify-between flex-shrink-0">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
              Roamora AI <span className="text-teal-500">✦</span>
            </h2>
            <p className="text-gray-600 text-xs sm:text-sm mt-0.5">Your intelligent travel companion</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-600 hidden sm:flex"><MicIcon size={15} /></span>
            <span className="text-gray-700 text-sm font-medium">Voice</span>
            <button
              onClick={() => setVoice(!voice)}
              aria-label="toggle voice"
              className={`relative rounded-full transition-colors duration-200 focus:outline-none flex-shrink-0 ${voice ? "bg-teal-500" : "bg-gray-300"}`}
              style={{ width: "48px", height: "26px" }}
            >
              <span className={`absolute top-[3px] left-[3px] w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 ${voice ? "translate-x-[22px]" : "translate-x-0"}`} />
            </button>
            <span className="text-sm font-semibold" style={{ minWidth: "28px", color: voice ? "#0d9488" : "#9ca3af" }}>
              {voice ? "On" : "Off"}
            </span>
          </div>
        </div>

        {/* AI Message Bubble */}
        <div className="rounded-2xl p-4 sm:p-5 flex-shrink-0" style={{ background: "rgba(255,255,255,0.55)", border: "1px solid rgba(255,255,255,0.6)" }}>
          <p className="font-bold text-gray-900 text-sm sm:text-base mb-1">Hello! 👋 I&apos;m Roamora AI</p>
          <p className="text-gray-700 text-xs sm:text-sm leading-relaxed">
            Tell me your destination, travel dates, budget, and travel style. I&apos;ll build your trip plan.
          </p>
          <p className="text-right text-xs text-gray-400 mt-2 sm:mt-3">11:19</p>
        </div>

        {/* Suggestions — flex-1 fills leftover space */}
        <div className="flex-1 flex flex-col justify-center">
          <p className="text-center text-gray-500 text-xs sm:text-sm mb-3">✦ Try asking me: ✦</p>
          <div className="flex flex-wrap gap-2 sm:gap-3 justify-center">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => setInput(s.text)}
                className="flex items-center gap-1.5 px-3 sm:px-5 py-2 sm:py-2.5 rounded-full text-xs sm:text-sm text-gray-700 hover:scale-105 transition-all"
                style={{ background: "rgba(255,255,255,0.6)", border: "1px solid rgba(255,255,255,0.7)" }}
              >
                <span>{s.icon}</span> {s.text}
              </button>
            ))}
          </div>
        </div>

        {/* Input Bar */}
        <div className="rounded-xl sm:rounded-2xl flex items-center gap-2 sm:gap-3 px-4 py-3 flex-shrink-0" style={{ background: "rgba(255,255,255,0.55)", border: "1px solid rgba(255,255,255,0.6)" }}>
          <button className="text-gray-400 hover:text-gray-600 text-xl font-light leading-none">+</button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about travel..."
            className="flex-1 outline-none text-sm text-gray-700 placeholder-gray-400 bg-transparent"
          />
          <button className="w-9 h-9 rounded-full border-2 border-teal-400 text-teal-500 hover:bg-teal-50 flex items-center justify-center transition-colors flex-shrink-0">
            <MicIcon size={15} />
          </button>
          <button className="bg-teal-600 text-white w-10 h-10 rounded-xl flex items-center justify-center hover:bg-teal-700 transition-colors flex-shrink-0">
            <SendIcon />
          </button>
        </div>

      </div>
      </div>
    </div>
  );
}
