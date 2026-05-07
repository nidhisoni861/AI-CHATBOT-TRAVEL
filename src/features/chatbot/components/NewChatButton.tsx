"use client";
import React from "react";
import { Plus } from "lucide-react";

export default function NewChatButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 px-3 py-1 rounded text-sm bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
    >
      <Plus size={14} />
      New
    </button>
  );
}
