"use client";

import Image from "next/image";
import { useState } from "react";
import {
  Camera,
  CheckCheck,
  Globe2,
  MoreHorizontal,
  Plus,
  Send,
  Sparkles,
} from "lucide-react";

type ChatRole = "user" | "ai";

type ChatMessage = {
  id: number;
  role: ChatRole;
  time: string;
  lines: string[];
  itinerary?: boolean;
};

function getTime() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getStarterMessage(): ChatMessage[] {
  return [
    {
      id: Date.now(),
      role: "ai",
      time: getTime(),
      lines: [
        "New chat started ✨",
        "Tell me your destination, travel dates, budget, and travel style. I’ll build your trip plan.",
      ],
    },
  ];
}

export default function ChatBotPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>(getStarterMessage);
  const [input, setInput] = useState("");

  function createNewChat() {
    setMessages(getStarterMessage());
    setInput("");
  }

  function createTripSuggestion(prompt: string) {
    const now = Date.now();

    setMessages([
      {
        id: now,
        role: "user",
        time: getTime(),
        lines: [prompt],
      },
      {
        id: now + 1,
        role: "ai",
        time: getTime(),
        itinerary: true,
        lines: getSuggestionResponse(prompt),
      },
    ]);

    setInput("");
  }

  function getSuggestionResponse(prompt: string) {
    if (prompt.includes("Berlin")) {
      return [
        "Great choice! Here’s a focused 1-day Berlin trip plan:",
        "☕ Morning — Brandenburg Gate, Reichstag, and Unter den Linden.",
        "🏛️ Afternoon — Museum Island or Berlin Wall Memorial.",
        "🌆 Evening — Alexanderplatz, street food, and dinner in Mitte.",
        "Would you like me to add exact timings, transport, and food stops?",
      ];
    }

    if (prompt.includes("Munich")) {
      return [
        "Perfect! Here’s a faster-paced 3-day Munich itinerary:",
        "🏙️ Day 1 — Marienplatz, Viktualienmarkt, English Garden, and Hofbräuhaus.",
        "🏰 Day 2 — Neuschwanstein Castle or Salzburg day trip.",
        "🚗 Day 3 — BMW Museum, Olympiapark, Nymphenburg Palace, and Bavarian food.",
        "Would you like me to turn this into a strict hour-by-hour schedule?",
      ];
    }

    return [
      "Amazing! Here’s a food-focused 5-day Stuttgart trip plan:",
      "🍽️ Day 1 — Schlossplatz, Königsstraße, Markthalle, and Swabian dinner.",
      "🚗 Day 2 — Mercedes-Benz Museum, Neckar views, and local cafés.",
      "🌳 Day 3 — Wilhelma, vineyards, Maultaschen, and Spätzle.",
      "🏰 Day 4 — Ludwigsburg Palace, food market, and relaxed evening.",
      "🥨 Day 5 — Porsche Museum, brunch spots, and final food experience.",
      "Would you like restaurant names, budget, and public transport routes?",
    ];
  }

  function sendMessage() {
    const trimmed = input.trim();

    if (!trimmed) return;

    const now = Date.now();

    setMessages((current) => [
      ...current,
      {
        id: now,
        role: "user",
        time: getTime(),
        lines: [trimmed],
      },
      {
        id: now + 1,
        role: "ai",
        time: getTime(),
        lines: [
          "Got it. I’ll use this preference to build a better travel plan.",
          "Tell me the city, number of days, pace, budget, and food preferences.",
        ],
      },
    ]);

    setInput("");
  }

  return (
    <section className="flex h-[calc(100vh-32px)] w-full max-w-[1040px] flex-col rounded-[34px] border border-white/75 bg-white/80 p-5 shadow-[0_28px_90px_rgba(15,23,42,0.24)] backdrop-blur-2xl sm:p-6 lg:p-7">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4 sm:gap-5">
          <div className="relative flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-100 to-white shadow-[0_16px_38px_rgba(20,184,166,0.28)] sm:h-[78px] sm:w-[78px]">
            <div className="absolute inset-0 rounded-full border-4 border-cyan-100/80" />
            <Image
              src="/images/robot-avatar.png"
              alt="Roamora AI robot avatar"
              width={58}
              height={58}
              className="relative object-contain"
              priority
            />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-extrabold tracking-tight text-slate-950 sm:text-4xl">
                Roamora AI
              </h1>
              <Sparkles className="h-7 w-7 text-teal-500" />
            </div>

            <p className="mt-1 text-base font-medium text-slate-500 sm:text-lg">
              Your intelligent travel companion
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full border border-white/80 bg-white/75 px-5 py-3 text-base font-bold text-teal-700 shadow-sm sm:flex">
            <span className="h-3 w-3 rounded-full bg-emerald-500 shadow-[0_0_12px_rgba(16,185,129,0.8)]" />
            Online
          </div>

          <button
            aria-label="Start new chat"
            onClick={createNewChat}
            className="flex h-12 w-12 items-center justify-center rounded-full bg-white/75 text-slate-600 shadow-sm transition hover:scale-105 hover:bg-white"
            title="Start new chat"
          >
            <MoreHorizontal className="h-6 w-6" />
          </button>
        </div>
      </header>

      <div className="mt-6 flex flex-1 flex-col justify-center gap-4 overflow-y-auto pr-1">
        {messages.map((message) => (
          <ChatBubble key={message.id} message={message} />
        ))}
      </div>

      <div className="mt-5 flex flex-wrap justify-center gap-3">
        <button
          onClick={() => createTripSuggestion("1 Day trip to Berlin")}
          className="rounded-full border border-teal-500/70 bg-white/60 px-5 py-3 text-sm font-extrabold text-teal-700 shadow-sm transition hover:bg-teal-50 sm:text-base"
        >
          1 Day trip to Berlin
        </button>

        <button
          onClick={() =>
            createTripSuggestion("3 day trip to Munich with faster pace")
          }
          className="rounded-full bg-white/80 px-5 py-3 text-sm font-bold text-slate-700 shadow-sm transition hover:bg-white sm:text-base"
        >
          3 day trip to Munich with faster pace
        </button>

        <button
          onClick={() =>
            createTripSuggestion(
              "5 day trip to Stuttgart with more food experiences"
            )
          }
          className="rounded-full bg-white/80 px-5 py-3 text-sm font-bold text-slate-700 shadow-sm transition hover:bg-white sm:text-base"
        >
          5 day trip to Stuttgart with more food experiences
        </button>
      </div>

      <footer className="mt-5 rounded-[26px] border border-white/70 bg-white/75 p-2 shadow-[0_12px_40px_rgba(15,23,42,0.08)]">
        <div className="flex items-center gap-2.5">
          <button
            aria-label="Create new chat"
            onClick={createNewChat}
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white text-slate-700 shadow-sm transition hover:scale-105"
            title="Create new chat"
          >
            <Plus className="h-6 w-6" />
          </button>

          <button
            aria-label="Travel language help"
            onClick={() =>
              createTripSuggestion("Help me with travel language phrases")
            }
            className="hidden h-12 w-12 shrink-0 items-center justify-center rounded-full text-slate-600 transition hover:bg-white sm:flex"
          >
            <Globe2 className="h-6 w-6" />
          </button>

          <button
            aria-label="Hotel help"
            onClick={() => createTripSuggestion("Help me find hotels")}
            className="hidden h-12 w-12 shrink-0 items-center justify-center rounded-full text-slate-600 transition hover:bg-white sm:flex"
          >
            <span className="text-xl">🛏️</span>
          </button>

          <button
            aria-label="Photo spots"
            onClick={() => createTripSuggestion("Suggest photo spots")}
            className="hidden h-12 w-12 shrink-0 items-center justify-center rounded-full text-slate-600 transition hover:bg-white sm:flex"
          >
            <Camera className="h-6 w-6" />
          </button>

          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") sendMessage();
            }}
            className="min-w-0 flex-1 bg-transparent px-2 text-base font-medium text-slate-700 outline-none placeholder:text-slate-500"
            placeholder="Ask anything about travel..."
          />

          <button
            aria-label="Send message"
            onClick={sendMessage}
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-700 to-cyan-700 text-white shadow-[0_14px_32px_rgba(13,148,136,0.35)] transition hover:scale-105"
          >
            <Send className="h-6 w-6" />
          </button>
        </div>
      </footer>
    </section>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[520px] rounded-[22px] rounded-tr-md bg-gradient-to-br from-teal-700 to-cyan-700 px-6 py-4 text-white shadow-[0_14px_30px_rgba(13,148,136,0.28)]">
          {message.lines.map((line) => (
            <p key={line} className="text-base font-bold leading-relaxed">
              {line}
            </p>
          ))}

          <div className="mt-2 flex items-center justify-end gap-2 text-xs text-white/80">
            <span>{message.time}</span>
            <CheckCheck className="h-4 w-4" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-4">
      <BotAvatarSmall />

      <div className="max-w-[720px] rounded-[22px] rounded-tl-md bg-white px-6 py-5 shadow-[0_14px_38px_rgba(15,23,42,0.10)]">
        {message.itinerary ? (
          <>
            <p className="text-base font-extrabold leading-relaxed text-slate-950">
              {message.lines[0]}
            </p>

            <div className="mt-3 space-y-2 text-base font-bold leading-relaxed text-slate-800">
              {message.lines.slice(1, -1).map((line) => (
                <p key={line}>{line}</p>
              ))}
            </div>

            <p className="mt-3 text-base font-bold leading-relaxed text-slate-900">
              {message.lines[message.lines.length - 1]}
            </p>
          </>
        ) : (
          <div className="space-y-4">
            {message.lines.map((line) => (
              <p
                key={line}
                className="text-base font-extrabold leading-relaxed text-slate-900 sm:text-lg"
              >
                {line}
              </p>
            ))}
          </div>
        )}

        <p className="mt-3 text-right text-sm font-medium text-slate-400">
          {message.time}
        </p>
      </div>
    </div>
  );
}

function BotAvatarSmall() {
  return (
    <div className="mt-2 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-cyan-50 shadow-[0_10px_26px_rgba(20,184,166,0.22)]">
      <Image
        src="/images/robot-avatar.png"
        alt="AI avatar"
        width={38}
        height={38}
        className="object-contain"
      />
    </div>
  );
}