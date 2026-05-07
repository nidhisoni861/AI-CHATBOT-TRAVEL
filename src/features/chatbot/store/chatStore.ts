"use client";
import create from "zustand";
import type { Chat, Message } from "@/src/features/chatbot/types/chat.types";
import type { StateCreator } from "zustand";

export type ChatState = {
  chats: Chat[];
  activeChatId?: string;
  typing: boolean;
  createChat: (title?: string) => string;
  setActive: (id: string) => void;
  addMessage: (chatId: string, message: { role: "user" | "bot"; text: string }) => Message;
  setTyping: (t: boolean) => void;
  ensureActiveChat: (title?: string) => string;
  updateChatTitle: (chatId: string, title: string) => void;
  reset: () => void;
};

function makeId() {
  return `${Date.now()}-${Math.floor(Math.random() * 100000)}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  chats: [],
  activeChatId: undefined,
  typing: false,

  createChat: (title?: string) => {
    const id = makeId();
    const chat: Chat = { id, title: title ?? "New chat", messages: [], createdAt: new Date().toISOString() };
    set((s: ChatState) => ({ chats: [chat, ...s.chats], activeChatId: id }));
    return id;
  },

  setActive: (id: string) => set({ activeChatId: id }),

  addMessage: (chatId: string, message: { role: "user" | "bot"; text: string }) => {
    const msg: Message = {
      id: makeId(),
      role: message.role,
      text: message.text,
      createdAt: new Date().toISOString(),
    };

    set((s: ChatState) => {
      const chats = s.chats.map((c: Chat) => {
        if (c.id === chatId) return { ...c, messages: [...c.messages, msg] };
        return c;
      });

      if (!chats.find((c: Chat) => c.id === chatId)) {
        const newChat: Chat = { id: chatId, title: "New chat", messages: [msg], createdAt: new Date().toISOString() };
        return { chats: [newChat, ...s.chats] };
      }
      return { chats };
    });

    return msg;
  },

  setTyping: (t: boolean) => set({ typing: t }),

  ensureActiveChat: (title?: string) => {
    const { activeChatId, createChat } = get();
    if (activeChatId) return activeChatId;
    return createChat(title);
  },

  updateChatTitle: (chatId: string, title: string) => {
    set((s: ChatState) => ({
      chats: s.chats.map((c: Chat) => (c.id === chatId ? { ...c, title: c.title && c.title !== "New chat" ? c.title : title } : c)),
    }));
  },

  reset: () => set({ chats: [], activeChatId: undefined, typing: false }),
} as any));
