import Image from "next/image";
import { Sparkles, Volume2, VolumeX } from "lucide-react";

interface ChatHeaderProps {
  voiceEnabled: boolean;
  onToggleVoice: () => void;
}

export function ChatHeader({ voiceEnabled, onToggleVoice }: ChatHeaderProps) {
  return (
    <header className="flex items-center justify-between gap-3">
      {/* Brand */}
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
            <h1 className="text-xl font-bold tracking-tight text-white sm:text-2xl">
              Roamora AI
            </h1>
            <Sparkles className="h-5 w-5 text-teal-300" />
          </div>
          <p className="mt-0.5 text-xs font-medium text-white/70 sm:text-sm">
            Your intelligent travel companion
          </p>
        </div>
      </div>

      {/* Voice TTS toggle */}
      <button
        onClick={onToggleVoice}
        aria-label={voiceEnabled ? "Turn voice off" : "Turn voice on"}
        className={`flex items-center gap-2 rounded-full border px-3 py-2 text-white shadow-[0_10px_24px_rgba(13,148,136,0.35)] transition-all duration-200 sm:gap-3 sm:px-4 sm:py-2.5 ${
          voiceEnabled
            ? "border-white/80 bg-teal-700"
            : "border-slate-300 bg-slate-400"
        }`}
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white/20 sm:h-8 sm:w-8">
          {voiceEnabled ? (
            <Volume2 className="h-4 w-4" />
          ) : (
            <VolumeX className="h-4 w-4" />
          )}
        </span>
        <span className="hidden text-xs font-bold sm:inline sm:text-sm">
          {voiceEnabled ? "Voice On" : "Voice Off"}
        </span>
        {/* Toggle pill */}
        <span className="relative h-6 w-11 rounded-full bg-white/30">
          <span
            className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-md transition-all duration-200 ${
              voiceEnabled ? "left-5" : "left-0.5"
            }`}
          />
        </span>
      </button>
    </header>
  );
}
