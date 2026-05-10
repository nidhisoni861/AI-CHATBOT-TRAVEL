"use client";

import { useRef, useState, useEffect } from "react";
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

async function callTranslate(
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

export default function ChatBotPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage()]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef(`session-${Date.now()}`);
  // Tracks the detected language across the conversation
  const userLangRef = useRef("en");

  const { voiceEnabled, isRecording, speak, toggleVoice, toggleRecording, setRecordingLang } =
    useVoice();

  // Speak welcome message on page load
  useEffect(() => {
    speak("Welcome to AI Travel Assistant. What can I help you with today?", "en");
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function newChat() {
    if (loading) return;
    sessionId.current = `session-${Date.now()}`;
    userLangRef.current = "en";
    setMessages([initialMessage()]);
    setInput("");
  }

  async function sendMessage(text?: string) {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;

    setMessages((prev) => [
      ...prev.filter((m) => m.id !== "init"),
      { id: `u-${Date.now()}`, role: "user", text: msg, time: makeTimestamp() },
    ]);
    setInput("");
    setLoading(true);

    try {
      // ── Step 1: Detect language & translate user message to English ───────────
      const { translated: englishMsg, detectedLang } = await callTranslate(msg, "en");
      userLangRef.current = detectedLang;
      setRecordingLang(detectedLang); // next voice input matches the detected language

      // ── Step 2: Send English message to the travel backend ───────────────────
      const backendRes = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: englishMsg, session_id: sessionId.current }),
      });
      if (!backendRes.ok) throw new Error("Backend error");

      const data = await backendRes.json() as {
        assistant_message?: string;
        dashboard_payload?: unknown;
        fallback_used?: boolean;
        parse_success?: boolean;
      };
      const englishReply =
        data.assistant_message ?? "I couldn't process that. Please try again.";

      // ── Step 3: Translate reply back to the user's language ──────────────────
      let displayReply = englishReply;
      if (detectedLang !== "en") {
        const { translated } = await callTranslate(englishReply, detectedLang);
        displayReply = translated;
      }

      // ── Step 4: Show in chat & speak aloud in the user's language ────────────
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: displayReply,
          time: makeTimestamp(),
          detectedLang,
          dashboard: (data.dashboard_payload as ChatMessage["dashboard"]) ?? null,
          showDashboard: !!data.dashboard_payload,
        },
      ]);

      speak(displayReply, detectedLang);
    } catch {
      const errMsg = "Something went wrong. Please check if the backend is running.";
      setMessages((prev) => [
        ...prev,
        { id: `e-${Date.now()}`, role: "assistant", text: errMsg, time: makeTimestamp() },
      ]);
      speak(errMsg, "en");
    } finally {
      setLoading(false);
    }
  }

  function handleToggleRecording() {
    // Voice transcript goes through the same detect → translate flow as typed text
    toggleRecording((transcript) => setInput(transcript));
  }

  return (
    <section className="flex h-full max-h-[calc(100vh-128px)] min-h-0 w-full max-w-[1220px] flex-col rounded-[28px] border border-white/15 bg-white/8 p-4 shadow-[0_28px_90px_rgba(0,0,0,0.20)] sm:rounded-[34px] sm:p-5 lg:p-6">
      <ChatHeader voiceEnabled={voiceEnabled} onToggleVoice={toggleVoice} />

      <ChatMessages messages={messages} loading={loading} />

      {messages.length === 1 && messages[0].id === "init" && (
        <SuggestionChips onSelect={sendMessage} disabled={loading} />
      )}

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
