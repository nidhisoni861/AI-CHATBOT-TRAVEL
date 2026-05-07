"use client";
import React, { useState } from "react";
import { Send } from "lucide-react";
import { useChat } from "@/src/features/chatbot/hooks/useChat";
import { sendMessageToApi } from "@/src/features/chatbot/services/chatService";
import { suggestedPrompts } from "@/src/features/chatbot/data/suggestedPrompts";

export default function ChatInput() {
  const [value, setValue] = useState("");
  const { activeChatId, ensureActiveChat, addMessage, setTyping, updateChatTitle } = useChat();

  const chatId = activeChatId ?? ensureActiveChat("Quick chat");

  async function onSend() {
    const text = value.trim();
    if (!text) return;
    setValue("");

    addMessage(chatId, { role: "user", text });
    updateChatTitle(chatId, text.slice(0, 30));

    setTyping(true);
    try {
      const res = await sendMessageToApi(text);
      addMessage(chatId, { role: "bot", text: res.reply });
    } catch {
      addMessage(chatId, { role: "bot", text: "Error: failed to fetch response." });
    } finally {
      setTyping(false);
    }
  }

  return (
    <div className="p-3 bg-gradient-to-b from-white to-zinc-50 dark:from-zinc-900 dark:to-zinc-900">
      <div className="max-w-3xl mx-auto flex flex-col gap-2">
        <div className="flex gap-2 items-center">
          <textarea
            rows={1}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Ask about travel, itineraries, or tips..."
            className="flex-1 resize-none bg-transparent outline-none text-sm px-3 py-2 rounded-full border border-zinc-200 dark:border-zinc-800"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
          />
          <button onClick={onSend} className="p-2 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
            <Send size={16} />
          </button>
        </div>

        <div className="flex gap-2 overflow-auto">
          {suggestedPrompts.slice(0, 4).map((p) => (
            <button key={p} onClick={() => setValue(p)} className="text-xs px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-800">
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
