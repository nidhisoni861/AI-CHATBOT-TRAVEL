"use client";
import React from "react";
import { motion } from "framer-motion";
import type { Message } from "@/src/features/chatbot/types/chat.types";

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className={`max-w-[85%] ${isUser ? "ml-auto bg-gradient-to-r from-blue-600 to-indigo-600 text-white" : "mr-auto bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-50"} p-3 rounded-2xl shadow-sm`}
    >
      <div className="whitespace-pre-wrap text-sm">{message.text}</div>
      <div className="text-[10px] text-zinc-400 mt-1 text-right">{new Date(message.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
    </motion.div>
  );
}
