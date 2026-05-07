"use client";
import React from "react";

export default function NewChatButton({ onClick }: { onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="inline-flex items-center gap-2 px-3 py-1 rounded text-sm bg-zinc-900 text-white dark:bg-zinc-50 dark:text-zinc-900"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="w-3 h-3"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M12 5v14M5 12h14"
        />
      </svg>
      New
    </button>
  );
}
