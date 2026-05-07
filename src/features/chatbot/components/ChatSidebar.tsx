"use client";
import React, { useState } from "react";
import { useChat } from "@/src/features/chatbot/hooks/useChat";
import NewChatButton from "@/src/features/chatbot/components/NewChatButton";
import type { Chat } from "@/src/features/chatbot/types/chat.types";

export default function ChatSidebar() {
  const { chats, activeChatId, setActive, createChat } = useChat();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile header */}
      <div className="md:hidden flex items-center justify-between px-3 py-2 border-b border-zinc-200 dark:border-zinc-800">
        <button
          aria-label="menu"
          onClick={() => setMobileOpen((v) => !v)}
          className="p-2 rounded hover:bg-zinc-100 dark:hover:bg-zinc-800"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
        <div className="text-sm font-medium">AI Travel</div>
        <NewChatButton onClick={() => createChat("Quick chat")} />
      </div>

      {/* Sidebar */}
      <aside
        className={`bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 md:flex flex-col w-72 transition-transform ${
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        } fixed md:relative top-0 left-0 bottom-0 z-40`}
      >
        <div className="p-4 flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800">
          <div className="font-semibold">Chats</div>
          <NewChatButton onClick={() => createChat("New chat")} />
        </div>

        <div className="overflow-auto flex-1">
          <ul>
            {chats.map((c: Chat) => (
              <li
                key={c.id}
                onClick={() => {
                  setActive(c.id);
                  setMobileOpen(false);
                }}
                className={`p-3 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800 ${
                  c.id === activeChatId ? "bg-zinc-100 dark:bg-zinc-900" : ""
                }`}
              >
                <div className="font-medium text-sm truncate">
                  {c.title ?? "Untitled"}
                </div>
                <div className="text-xs text-zinc-500">
                  {c.messages.length} messages
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="p-3 border-t border-zinc-100 dark:border-zinc-800">
          <button
            onClick={() => createChat("New chat")}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
          >
            New Chat
          </button>
        </div>
      </aside>

      {/* spacer so layout aligns on desktop */}
      <div className="md:ml-72" />
    </>
  );
}
