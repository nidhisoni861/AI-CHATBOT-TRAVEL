"use client";
import React, { useEffect, useRef } from "react";
import { useChat } from "@/src/features/chatbot/hooks/useChat";
import ChatMessage from "@/src/features/chatbot/components/ChatMessage";
import ChatInput from "@/src/features/chatbot/components/ChatInput";
import BotTypingIndicator from "@/src/features/chatbot/components/BotTypingIndicator";

export default function ChatWindow() {
  const { activeChat, typing } = useChat();
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [activeChat?.messages.length, typing]);

  if (!activeChat) {
    return <div className="h-full flex items-center justify-center text-sm text-zinc-500">No chat selected</div>;
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-2 text-xs text-zinc-500 border-b border-zinc-100 dark:border-zinc-800">Chat: {activeChat.title}</div>

      <div ref={scrollerRef} className="flex-1 overflow-auto px-4 py-6 space-y-4">
        {activeChat.messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}

        {typing && <BotTypingIndicator />}
      </div>

      <div className="border-t border-zinc-100 dark:border-zinc-800">
        <ChatInput />
      </div>
    </div>
  );
}
