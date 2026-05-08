"use client";
import React, { useState, useEffect, useRef } from "react";
import AnimatedRobot from "@/src/features/dashboard/components/AnimatedRobot";
import { useChat } from "@/src/features/chatbot/hooks/useChat";
import { sendMessageToApi } from "@/src/features/chatbot/services/chatService";
import type { Message } from "@/src/features/chatbot/types/chat.types";

export default function AiAssistantCard() {
  const { activeChat, activeChatId, createChat, addMessage, setTyping, typing } = useChat();
  const [value, setValue] = useState("");
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollerRef.current) scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight;
  }, [activeChat?.messages.length, typing]);

  const chatId = activeChatId ?? createChat("Welcome Chat");

  async function onSend() {
    const text = value.trim();
    if (!text) return;
    setValue("");

    // add user message locally
    addMessage(chatId, { role: "user", text });
    setTyping(true);

    try {
      const res = await sendMessageToApi(text);
      addMessage(chatId, { role: "bot", text: res.reply });
    } catch (e) {
      addMessage(chatId, { role: "bot", text: "Error: failed to get reply." });
    } finally {
      setTyping(false);
    }
  }

  return (
    <div className="rounded-3xl bg-white/55 backdrop-blur-2xl border border-white/60 p-6 shadow-[0_30px_100px_rgba(99,102,241,0.12)] hover:-translate-y-1 transition-transform">
      <div className="flex flex-col items-center">
        <AnimatedRobot />
        <h2 className="mt-4 text-3xl font-semibold text-slate-700">Hello, Traveler! <span className="text-2xl">👋</span></h2>
        <p className="text-sm text-slate-500 mt-2">How can I help you plan your next adventure?</p>
        {activeChat && (
          <div className="text-xs text-zinc-500 mt-1">Active chat: <span className="font-medium">{activeChat.title}</span></div>
        )}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4">
        {[
          { title: "Plan a trip", subtitle: "Personalized itineraries", emoji: "🧭" },
          { title: "Find stays", subtitle: "Hotels & unique stays", emoji: "🏨" },
          { title: "Explore attractions", subtitle: "Top sights & hidden gems", emoji: "🏛️" },
          { title: "Check travel tips", subtitle: "Smart tips & safety", emoji: "📝" },
        ].map((a) => (
          <button
            key={a.title}
            onClick={() => {
              const q = `${a.title} - ${a.subtitle}`;
              addMessage(chatId, { role: "user", text: q });
              setTyping(true);
              sendMessageToApi(q)
                .then((res) => addMessage(chatId, { role: "bot", text: res.reply }))
                .catch(() => addMessage(chatId, { role: "bot", text: "Error: failed to fetch" }))
                .finally(() => setTyping(false));
            }}
            className="p-4 rounded-xl bg-white/6 backdrop-blur-sm hover:scale-105 transition-transform flex items-start gap-3"
          >
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-violet-600 to-sky-500 flex items-center justify-center text-white text-xl">{a.emoji}</div>
            <div className="text-left">
              <div className="text-sm font-medium text-slate-700">{a.title}</div>
              <div className="text-xs text-slate-500">{a.subtitle}</div>
            </div>
          </button>
        ))}
      </div>

      <div className="mt-6">
        <div ref={scrollerRef} className="rounded-2xl p-4 bg-gradient-to-r from-indigo-50 to-sky-50 text-slate-700 max-h-48 overflow-auto">
          {activeChat?.messages.length ? (
            activeChat.messages.map((m: Message) => (
              <div key={m.id} className={`mb-3 max-w-[80%] ${m.role === "user" ? "ml-auto bg-gradient-to-r from-blue-600 to-indigo-600 text-white" : "mr-auto bg-white/80 text-slate-900"} p-3 rounded-2xl`}>{m.text}</div>
            ))
          ) : (
            <div className="text-sm text-slate-600">I can help you discover amazing places, plan itineraries, find stays, and much more. What are you thinking about?</div>
          )}

          {typing && <div className="mt-2 text-sm text-slate-500">WanderAI is typing...</div>}
        </div>

        <div className="mt-4">
          <div className="flex items-center gap-3 bg-white/5 border border-white/6 rounded-full px-3 py-2">
            <button className="p-2 rounded-full bg-white/6">+</button>
            <input value={value} onChange={(e) => setValue(e.target.value)} className="flex-1 bg-transparent outline-none text-sm" placeholder="Ask anything about your trip..." onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); onSend(); } }} />
            <button className="p-2">🎤</button>
            <button onClick={onSend} className="px-4 py-2 rounded-full bg-gradient-to-br from-violet-600 to-sky-500 text-white hover:scale-105 transition-transform">Send</button>
          </div>
          <div className="text-xs text-slate-500 mt-2">WanderAI can make mistakes. Please verify important information.</div>
        </div>
      </div>
    </div>
  );
}
