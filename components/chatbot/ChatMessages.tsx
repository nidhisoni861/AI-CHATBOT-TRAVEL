"use client";

import Image from "next/image";
import { CheckCheck } from "lucide-react";
import { useEffect, useRef } from "react";
import { DashboardCards } from "./DashboardCards";
import { TypingIndicator } from "./TypingIndicator";
import type { ChatMessage } from "./types";

interface ChatMessagesProps {
  messages: ChatMessage[];
  loading: boolean;
}

export function ChatMessages({ messages, loading }: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="mt-4 flex flex-1 flex-col gap-3 overflow-y-auto pr-1 sm:mt-5">
      {messages.map((msg) =>
        msg.role === "user" ? (
          /* User bubble — right aligned */
          <div key={msg.id} className="flex justify-end">
            <div className="max-w-[80%] rounded-[18px] rounded-tr-md bg-gradient-to-br from-teal-700 to-cyan-700 px-4 py-3 text-white shadow-[0_10px_24px_rgba(13,148,136,0.28)] sm:max-w-[480px] sm:px-5">
              <p className="text-sm font-medium leading-relaxed">{msg.text}</p>
              <div className="mt-1.5 flex items-center justify-end gap-1.5 text-xs text-white/80">
                <span>{msg.time}</span>
                <CheckCheck className="h-3.5 w-3.5" />
              </div>
            </div>
          </div>
        ) : (
          /* Assistant bubble — left aligned */
          <div key={msg.id} className="flex items-start gap-2.5 sm:gap-3">
            <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cyan-50 shadow-[0_8px_20px_rgba(20,184,166,0.22)] sm:h-10 sm:w-10">
              <Image
                src="/avatar.jpeg"
                alt="AI avatar"
                width={36}
                height={36}
                className="h-full w-full rounded-full object-cover"
              />
            </div>
            <div className="min-w-0 max-w-[85%] flex-1 sm:max-w-[680px]">
              {/* Always show the translated text response */}
              <div className="rounded-[18px] rounded-tl-md bg-white/10 px-4 py-3 shadow-[0_10px_30px_rgba(15,23,42,0.10)] sm:px-5 sm:py-4">
                <p className="whitespace-pre-line text-sm leading-relaxed text-white">
                  {msg.text}
                </p>
                <p className="mt-2 text-right text-xs font-medium text-white/60">
                  {msg.time}
                </p>
              </div>
              {/* Show dashboard cards below the text if available */}
              {msg.showDashboard && msg.dashboard && (
                <div className="mt-3">
                  <DashboardCards payload={msg.dashboard} lang={msg.detectedLang} />
                </div>
              )}
            </div>
          </div>
        )
      )}

      {/* Typing indicator */}
      {loading && (
        <div className="flex items-start gap-2.5 sm:gap-3">
          <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cyan-50 shadow-[0_8px_20px_rgba(20,184,166,0.22)] sm:h-10 sm:w-10">
            <Image
              src="/avatar.jpeg"
              alt="AI avatar"
              width={36}
              height={36}
              className="h-full w-full rounded-full object-cover"
            />
          </div>
          <div className="rounded-[18px] rounded-tl-md bg-white/10 shadow-[0_10px_30px_rgba(15,23,42,0.10)]">
            <TypingIndicator />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
