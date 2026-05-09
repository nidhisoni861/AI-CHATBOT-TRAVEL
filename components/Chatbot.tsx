import Image from "next/image";
import {
  Camera,
  CalendarDays,
  CheckCheck,
  Mic,
  Paperclip,
  Plus,
  Send,
  Sparkles,
  Utensils,
} from "lucide-react";

export default function ChatBotPanel() {
  return (
    <section className="flex h-full max-h-[calc(100vh-128px)] min-h-0 w-full max-w-[1220px] flex-col rounded-[28px] border border-white/75 bg-white/80 p-4 shadow-[0_28px_90px_rgba(15,23,42,0.24)] backdrop-blur-2xl sm:rounded-[34px] sm:p-5 lg:p-6">
      {/* Header */}
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 sm:gap-4">
          <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-100 to-white shadow-[0_12px_28px_rgba(20,184,166,0.28)] sm:h-14 sm:w-14">
            <div className="absolute inset-0 rounded-full border-[3px] border-cyan-100/80" />
            <Image
              src="/avatar.jpeg"
              alt="AI avatar"
              width={44}
              height={44}
              className="relative h-full w-full rounded-full object-cover"
              priority
            />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-xl font-bold tracking-tight text-slate-950 sm:text-2xl">
                Roamora AI
              </h1>
              <Sparkles className="h-5 w-5 text-teal-500" />
            </div>
            <p className="mt-0.5 text-xs font-medium text-slate-500 sm:text-sm">
              Your intelligent travel companion
            </p>
          </div>
        </div>

        {/* Static Voice Toggle Design */}
        <div className="flex items-center gap-2 rounded-full border border-white/80 bg-teal-700 px-3 py-2 text-white shadow-[0_10px_24px_rgba(13,148,136,0.35)] sm:gap-3 sm:px-4 sm:py-2.5">
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20 sm:h-8 sm:w-8">
            <Mic className="h-4 w-4" />
          </span>

          <span className="hidden text-xs font-bold sm:inline sm:text-sm">
            Voice On
          </span>

          <span className="relative h-6 w-11 rounded-full bg-white/30">
            <span className="absolute left-5 top-0.5 h-5 w-5 rounded-full bg-white shadow-md" />
          </span>
        </div>
      </header>

      {/* Chat Area */}
      <div className="mt-4 flex flex-1 flex-col justify-center gap-3 overflow-y-auto pr-1 sm:mt-5 sm:gap-4">
        {/* AI Message */}
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

          <div className="max-w-[85%] rounded-[18px] rounded-tl-md bg-white px-4 py-3 shadow-[0_10px_30px_rgba(15,23,42,0.10)] sm:max-w-[680px] sm:px-5 sm:py-4">
            <div className="space-y-2">
              <p className="text-sm font-semibold leading-relaxed text-slate-900">
                New chat started ✨
              </p>
              <p className="text-sm font-normal leading-relaxed text-slate-700">
                Tell me your destination, travel dates, budget, and travel
                style. I&apos;ll build your trip plan.
              </p>
            </div>

            <p className="mt-2 text-right text-xs font-medium text-slate-400">
              11:16
            </p>
          </div>
        </div>

        {/* Example User Message */}
        <div className="flex justify-end">
          <div className="max-w-[80%] rounded-[18px] rounded-tr-md bg-gradient-to-br from-teal-700 to-cyan-700 px-4 py-3 text-white shadow-[0_10px_24px_rgba(13,148,136,0.28)] sm:max-w-[480px] sm:px-5">
            <p className="text-sm font-medium leading-relaxed">
              I want a 3 day trip to Munich with faster pace.
            </p>

            <div className="mt-1.5 flex items-center justify-end gap-1.5 text-xs text-white/80">
              <span>11:18</span>
              <CheckCheck className="h-3.5 w-3.5" />
            </div>
          </div>
        </div>
      </div>

      {/* Suggestions */}
      <div className="mt-4 flex flex-wrap justify-center gap-2 sm:gap-3">
        <button className="flex items-center gap-1.5 rounded-full border border-teal-500/70 bg-white/60 px-3 py-2 text-xs font-semibold text-teal-700 shadow-sm transition hover:bg-white/90 sm:px-4 sm:py-2.5 sm:text-sm">
          <CalendarDays className="h-4 w-4" />
          1 Day trip to Berlin
        </button>

        <button className="flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-white/90 sm:px-4 sm:py-2.5 sm:text-sm">
          <CalendarDays className="h-4 w-4" />
          3 day trip to Munich with faster pace
        </button>

        <button className="flex items-center gap-1.5 rounded-full bg-white/80 px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:bg-white/90 sm:px-4 sm:py-2.5 sm:text-sm">
          <Utensils className="h-4 w-4" />
          5 day trip to Stuttgart with more food experiences
        </button>
      </div>

      {/* Input Area - Static Design Only */}
      <footer className="mt-4 rounded-[22px] border border-white/70 bg-white/75 p-1.5 shadow-[0_12px_40px_rgba(15,23,42,0.08)] sm:mt-5 sm:p-2">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <button
            type="button"
            aria-label="Add"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-slate-700 shadow-sm sm:h-11 sm:w-11"
          >
            <Plus className="h-5 w-5" />
          </button>

          <button
            type="button"
            aria-label="Attach files"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-slate-600 sm:h-11 sm:w-11"
          >
            <Paperclip className="h-5 w-5" />
          </button>

          <button
            type="button"
            aria-label="Camera"
            className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-full text-slate-600 sm:flex sm:h-11 sm:w-11"
          >
            <Camera className="h-5 w-5" />
          </button>

          <div className="min-w-0 flex-1 bg-transparent px-2 text-sm font-medium text-slate-500">
            Ask anything about travel...
          </div>

          <button
            type="button"
            aria-label="Voice input"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-slate-700 shadow-sm sm:h-11 sm:w-11"
          >
            <Mic className="h-5 w-5" />
          </button>

          <button
            type="button"
            aria-label="Send message"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-700 to-cyan-700 text-white shadow-[0_10px_24px_rgba(13,148,136,0.35)] sm:h-12 sm:w-12"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </footer>
    </section>
  );
}