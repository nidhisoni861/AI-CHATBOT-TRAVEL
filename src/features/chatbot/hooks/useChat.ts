"use client";
import { useCallback } from "react";
import { useChatStore, type ChatState } from "@/src/features/chatbot/store/chatStore";
import type { Chat } from "@/src/features/chatbot/types/chat.types";

export function useChat() {
  const chats = useChatStore((s: ChatState) => s.chats);
  const activeChatId = useChatStore((s: ChatState) => s.activeChatId);
  const typing = useChatStore((s: ChatState) => s.typing);

  const createChat = useChatStore((s: ChatState) => s.createChat);
  const setActive = useChatStore((s: ChatState) => s.setActive);
  const addMessage = useChatStore((s: ChatState) => s.addMessage);
  const setTyping = useChatStore((s: ChatState) => s.setTyping);
  const ensureActiveChat = useChatStore((s: ChatState) => s.ensureActiveChat);
  const updateChatTitle = useChatStore((s: ChatState) => s.updateChatTitle);

  const activeChat: Chat | undefined = chats.find((c: Chat) => c.id === activeChatId) ?? chats[0];

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
