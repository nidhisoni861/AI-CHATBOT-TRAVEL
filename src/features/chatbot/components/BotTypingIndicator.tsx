"use client";
import React from "react";
import { motion } from "framer-motion";

export default function BotTypingIndicator() {
  const bounce = { y: [0, -6, 0], transition: { duration: 0.8, repeat: Infinity, ease: "easeInOut" } };
  return (
    <div className="mr-auto bg-zinc-100 dark:bg-zinc-800 p-2 rounded-lg max-w-[30%]">
      <div className="flex items-end gap-2">
        <motion.span className="w-2 h-2 rounded-full bg-zinc-600" animate={bounce} style={{ transitionDelay: "0s" }} />
        <motion.span className="w-2 h-2 rounded-full bg-zinc-600" animate={bounce} style={{ transitionDelay: "0.12s" }} />
        <motion.span className="w-2 h-2 rounded-full bg-zinc-600" animate={bounce} style={{ transitionDelay: "0.24s" }} />
      </div>
    </div>
  );
}
