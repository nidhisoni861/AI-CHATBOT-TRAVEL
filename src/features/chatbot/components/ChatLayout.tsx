"use client";
import React, { useEffect } from "react";
import { useChat } from "@/src/features/chatbot/hooks/useChat";
import ChatSidebar from "@/src/features/chatbot/components/ChatSidebar";
import ChatWindow from "@/src/features/chatbot/components/ChatWindow";

export function ChatLayout() {
  const { chats, createChat } = useChat();

  useEffect(() => {
    if (chats.length === 0) createChat("Welcome Chat");
  }, [chats.length, createChat]);

  return (
    <div className="min-h-screen flex bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-zinc-50">
      <ChatSidebar />
      <div className="flex-1 flex flex-col">
        <header className="h-14 flex items-center justify-between px-4 border-b border-zinc-200 dark:border-zinc-800">
          <div className="flex flex-col">
            <span className="text-lg font-semibold">AI Travel — Navigator</span>
            <span className="text-xs text-zinc-500">
              Futuristic travel assistant
            </span>
          </div>
        </header>
        <main className="flex-1 overflow-hidden">
          <ChatWindow />
        </main>
      </div>
    </div>
  );
}

export default ChatLayout;