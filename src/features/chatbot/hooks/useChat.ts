"use client";
import { useCallback } from "react";
import { useChatStore } from "@/src/features/chatbot/store/chatStore";
import type { Chat } from "@/src/features/chatbot/types/chat.types";

export function useChat() {
  const chats = useChatStore((s: any) => s.chats as Chat[]);
  const activeChatId = useChatStore((s: any) => s.activeChatId as string | undefined);
  const typing = useChatStore((s: any) => s.typing as boolean);

  const createChat = useChatStore((s: any) => s.createChat as (title?: string) => string);
  const setActive = useChatStore((s: any) => s.setActive as (id: string) => void);
  const addMessage = useChatStore((s: any) => s.addMessage as (chatId: string, message: { role: "user" | "bot"; text: string }) => any);
  const setTyping = useChatStore((s: any) => s.setTyping as (t: boolean) => void);
  const ensureActiveChat = useChatStore((s: any) => s.ensureActiveChat as (title?: string) => string);
  const updateChatTitle = useChatStore((s: any) => s.updateChatTitle as (chatId: string, title: string) => void);

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
