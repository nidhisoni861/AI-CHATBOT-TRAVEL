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
  };
}

export default function ChatBotPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage()]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useRef(`session-${Date.now()}`);

  const { voiceEnabled, isRecording, speak, toggleVoice, toggleRecording } =
    useVoice();

  // Speak welcome on every page load / reload
  useEffect(() => {
    speak("Welcome to AI Travel Assistant. What can I help you with today?");
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function newChat() {
    if (loading) return;
    sessionId.current = `session-${Date.now()}`;
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
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: sessionId.current }),
      });

      if (!res.ok) throw new Error("Backend error");

      const data = await res.json();
      const assistantText =
        data.assistant_message ?? "I couldn't process that. Please try again.";

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          text: assistantText,
          time: makeTimestamp(),
          dashboard: data.dashboard_payload ?? null,
          showDashboard: !!data.dashboard_payload,
        },
      ]);

      // Speak assistant reply if voice is on
      speak(assistantText);
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
        },
      ]);
      speak(errorText);
    } finally {
      setLoading(false);
    }
  }

  function handleToggleRecording() {
    // On recognition result → fill the input field
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
