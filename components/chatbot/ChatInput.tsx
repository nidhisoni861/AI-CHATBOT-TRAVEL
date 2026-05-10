import { KeyboardEvent } from "react";
import { Loader2, Mic, MicOff, Paperclip, Plus, Send } from "lucide-react";

interface ChatInputProps {
  input: string;
  loading: boolean;
  isRecording: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onNewChat: () => void;
  onToggleRecording: () => void;
}

export function ChatInput({
  input,
  loading,
  isRecording,
  onInputChange,
  onSend,
  onNewChat,
  onToggleRecording,
}: ChatInputProps) {
  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  function getPlaceholder() {
    if (isRecording && !input) return "Listening… click mic again to stop";
    if (isRecording && input) return "Transcribing…";
    return "Ask anything about travel...";
  }

  return (
    <footer className="mt-4 rounded-[22px] border border-white/70 bg-white/75 p-1.5 shadow-[0_12px_40px_rgba(15,23,42,0.08)] sm:mt-5 sm:p-2">
      <div className="flex items-center gap-1.5 sm:gap-2">
        {/* New chat */}
        <button
          type="button"
          aria-label="New chat"
          onClick={onNewChat}
          disabled={loading}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white text-slate-700 shadow-sm transition hover:bg-teal-50 hover:text-teal-700 disabled:opacity-50 sm:h-11 sm:w-11"
        >
          <Plus className="h-5 w-5" />
        </button>

        {/* Attach */}
        <button
          type="button"
          aria-label="Attach files"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-slate-600 transition hover:text-teal-700 sm:h-11 sm:w-11"
        >
          <Paperclip className="h-5 w-5" />
        </button>

        {/* Text input */}
        <textarea
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={handleKey}
          placeholder={getPlaceholder()}
          rows={1}
          disabled={loading}
          className="min-w-0 flex-1 resize-none bg-transparent px-2 text-sm font-medium text-slate-800 placeholder-slate-400 focus:outline-none disabled:opacity-50"
        />

        {/* Mic / STT — red + pulse while recording, amber + spinner while transcribing */}
        <button
          type="button"
          aria-label={isRecording ? "Stop & transcribe" : "Start voice input"}
          onClick={onToggleRecording}
          disabled={loading}
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl shadow-sm transition sm:h-11 sm:w-11 ${
            isRecording && !input
              ? "animate-pulse bg-red-500 text-white"
              : isRecording && input
              ? "bg-amber-400 text-white"
              : "bg-white text-slate-700 hover:text-teal-700"
          }`}
        >
          {isRecording && input ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : isRecording ? (
            <MicOff className="h-5 w-5" />
          ) : (
            <Mic className="h-5 w-5" />
          )}
        </button>

        {/* Send */}
        <button
          type="button"
          aria-label="Send message"
          onClick={() => onSend()}
          disabled={loading || !input.trim()}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-700 to-cyan-700 text-white shadow-[0_10px_24px_rgba(13,148,136,0.35)] transition disabled:opacity-50 sm:h-12 sm:w-12"
        >
          <Send className="h-5 w-5" />
        </button>
      </div>
    </footer>
  );
}
