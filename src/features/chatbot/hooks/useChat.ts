"use client";
import { useCallback } from "react";
import { useChatStore } from "@/src/features/chatbot/store/chatStore";
import type { Chat } from "@/src/features/chatbot/types/chat.types";

export function useChat() {
  const chats = useChatStore((s) => s.chats);
  const activeChatId = useChatStore((s) => s.activeChatId);
  const typing = useChatStore((s) => s.typing);

  const createChat = useChatStore((s) => s.createChat);
  const setActive = useChatStore((s) => s.setActive);
  const addMessage = useChatStore((s) => s.addMessage);
  const setTyping = useChatStore((s) => s.setTyping);
  const ensureActiveChat = useChatStore((s) => s.ensureActiveChat);
  const updateChatTitle = useChatStore((s) => s.updateChatTitle);

  const activeChat: Chat | undefined = chats.find((c) => c.id === activeChatId) ?? chats[0];

  const ensureActive = useCallback((title?: string) => ensureActiveChat(title), [ensureActiveChat]);

  return {
    chats,
    activeChat,
    activeChatId,
    typing,
    createChat,
    setActive,
    addMessage,
    setTyping,
    ensureActiveChat: ensureActive,
    ensureActiveChatRaw: ensureActiveChat,
    ensureActive,
    updateChatTitle,
  };
}
