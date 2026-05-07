"use client";
import React from "react";

export default function BotTypingIndicator() {
  return (
    <div className="mr-auto bg-zinc-100 dark:bg-zinc-800 p-2 rounded-lg max-w-[30%]">
      <div className="flex items-end gap-2">
        <span className="w-2 h-2 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: "0s" }} />
        <span className="w-2 h-2 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: "0.12s" }} />
        <span className="w-2 h-2 rounded-full bg-zinc-600 animate-bounce" style={{ animationDelay: "0.24s" }} />
      </div>
    </div>
  );
}
