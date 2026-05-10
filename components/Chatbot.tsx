"use client";

import { useRef, useState } from "react";
import { ChatHeader } from "./chatbot/ChatHeader";
import { ChatInput } from "./chatbot/ChatInput";
import { ChatMessages } from "./chatbot/ChatMessages";
import { SuggestionChips } from "./chatbot/SuggestionChips";
import { useVoice } from "./chatbot/hooks/useVoice";
import type { ChatMessage } from "./chatbot/types";

function makeTimestamp() {
  return new Date().toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function initialMessage(): ChatMessage {
  return {
    id: "init",
    role: "assistant",
    text: "New chat started ✨\n\nTell me your destination, travel dates, budget, and travel style. I'll build your trip plan.",
    time: makeTimestamp(),
    detectedLang: "en",
  };
}

// ─── Translation helpers ──────────────────────────────────────────────────────

async function translateText(
  text: string,
  targetLang: string
): Promise<{ translated: string; detectedLang: string }> {
  const res = await fetch("/api/translate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, targetLang }),
  });
  if (!res.ok) return { translated: text, detectedLang: targetLang };
  return res.json() as Promise<{ translated: string; detectedLang: string }>;
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function ChatBotPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage()]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef(`session-${Date.now()}`);
  // Language detected from the most recent voice input (Whisper gives this for free)
  const pendingVoiceLang = useRef<string | null>(null);

  const { voiceEnabled, isRecording, speak, toggleVoice, toggleRecording } =
    useVoice();

  function newChat() {
    if (loading) return;
    sessionId.current = `session-${Date.now()}`;
    setMessages([initialMessage()]);
    setInput("");
    pendingVoiceLang.current = null;
  }

  async function sendMessage(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    // Grab and clear the voice-detected language before any state updates
    const voiceLang = pendingVoiceLang.current;
    pendingVoiceLang.current = null;

    setMessages((prev) => [
      ...prev.filter((m) => m.id !== "init"),
      { id: `u-${Date.now()}`, role: "user", text: msg, time: makeTimestamp() },
    ]);
    setInput("");
    setLoading(true);

    try {
      // ── Step 1: Detect language & translate user message to English ──────────
      let detectedLang = voiceLang ?? "en";
      let msgForBackend = msg;

      if (voiceLang && voiceLang !== "en") {
        // Whisper already told us the language — just translate to English
        const { translated } = await translateText(msg, "en");
        msgForBackend = translated;
      } else if (!voiceLang) {
        // Typed text — detect language + translate in one call
        const result = await translateText(msg, "en");
        detectedLang = result.detectedLang;
        msgForBackend = detectedLang !== "en" ? result.translated : msg;
      }

      // ── Step 2: Send English to YOUR travel backend (unchanged) ─────────────
      const backendRes = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msgForBackend,
          session_id: sessionId.current,
        }),
      });
      if (!backendRes.ok) throw new Error("Backend error");

      const backendData = await backendRes.json() as {
        assistant_message?: string;
        dashboard_payload?: unknown;
        fallback_used?: boolean;
        parse_success?: boolean;
      };
      const englishResponse =
        backendData.assistant_message ??
        "I couldn't process that. Please try again.";

      // ── Step 3: Translate backend response back to detected language ─────────
      let displayResponse = englishResponse;
      if (detectedLang !== "en") {
        const { translated } = await translateText(englishResponse, detectedLang);
        displayResponse = translated;
      }

      // ── Step 4: Display & speak ──────────────────────────────────────────────
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: displayResponse,
          time: makeTimestamp(),
          detectedLang,
          dashboard: (backendData.dashboard_payload as ChatMessage["dashboard"]) ?? null,
          showDashboard:
            !backendData.fallback_used &&
            backendData.parse_success &&
            !!backendData.dashboard_payload,
        },
      ]);

      speak(displayResponse, detectedLang);
    } catch {
      const errorText =
        "Something went wrong. Please check if the backend is running.";
      setMessages((prev) => [
        ...prev,
        {
          id: `e-${Date.now()}`,
          role: "assistant",
          text: errorText,
          time: makeTimestamp(),
          detectedLang: "en",
        },
      ]);
      speak(errorText, "en");
    } finally {
      setLoading(false);
    }
  }

  function handleToggleRecording() {
    toggleRecording((transcript, detectedLang) => {
      // Called by Whisper when transcription is ready
      setInput(transcript);
      pendingVoiceLang.current = detectedLang;
    });
  }

  return (
    <section className="flex h-full max-h-[calc(100vh-128px)] min-h-0 w-full max-w-[1220px] flex-col rounded-[28px] border border-white/75 bg-white/80 p-4 shadow-[0_28px_90px_rgba(15,23,42,0.24)] backdrop-blur-2xl sm:rounded-[34px] sm:p-5 lg:p-6">
      <ChatHeader voiceEnabled={voiceEnabled} onToggleVoice={toggleVoice} />

      <ChatMessages messages={messages} loading={loading} />

      <SuggestionChips onSelect={sendMessage} disabled={loading} />

      <ChatInput
        input={input}
        loading={loading}
        isRecording={isRecording}
        onInputChange={setInput}
        onSend={sendMessage}
        onNewChat={newChat}
        onToggleRecording={handleToggleRecording}
      />
    </section>
  );
}
