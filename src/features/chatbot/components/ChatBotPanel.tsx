"use client";
import Image from "next/image";
import { useRef, useState, type ChangeEvent } from "react";
import { CheckCheck, Mic, MicOff, Paperclip, Plus, Send, Sparkles, X } from "lucide-react";

type Role = "user" | "ai";
type ChatMessage = { id: number; role: Role; time: string; lines: string[] };
type SR = { continuous: boolean; interimResults: boolean; lang: string; start(): void; stop(): void; onresult: ((e: any) => void) | null; onerror: ((e: Event) => void) | null; onend: (() => void) | null };
type SRCtor = new () => SR;
declare global { interface Window { SpeechRecognition?: SRCtor; webkitSpeechRecognition?: SRCtor } }

const now = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const starter: ChatMessage[] = [{ id: 1, role: "ai", time: "11:16", lines: ["New chat started ✨", "Tell me your destination, travel dates, budget, and travel style. I’ll build your trip plan."] }];
const suggestions = ["1 Day trip to Berlin", "3 day trip to Munich with faster pace", "5 day trip to Stuttgart with more food experiences"];

export default function ChatBotPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>(starter);
  const [input, setInput] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [voiceOn, setVoiceOn] = useState(false);
  const [listening, setListening] = useState(false);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const recRef = useRef<SR | null>(null);

  const stopListening = () => { recRef.current?.stop(); recRef.current = null; setListening(false); };
  const toggleVoice = () => setVoiceOn((v) => { if (v) stopListening(); return !v; });
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(e.target.files ?? []);
    if (selected.length) setFiles((current) => [...current, ...selected]);
    e.target.value = "";
  };
  const startListening = () => {
    const API = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!API) return setMessages((m) => [...m, { id: Date.now(), role: "ai", time: now(), lines: ["Voice input is not supported in this browser.", "Please try Chrome or Edge for speech recognition."] }]);
    const rec = new API();
    rec.continuous = false; rec.interimResults = true; rec.lang = "en-US";
    rec.onresult = (e) => { let text = ""; for (let i = e.resultIndex; i < e.results.length; i++) text += e.results[i][0].transcript; setInput(text); };
    rec.onerror = () => setListening(false); rec.onend = () => setListening(false);
    recRef.current = rec; setVoiceOn(true); setListening(true); rec.start();
  };
  const toggleListening = () => listening ? stopListening() : startListening();
  const sendMessage = () => {
    const text = input.trim();
    if (!text && !files.length) return;
    setMessages((m) => [...m, { id: Date.now(), role: "user", time: now(), lines: [...(text ? [text] : []), ...files.map((f) => `Attached file: ${f.name}`)] }]);
    setInput(""); setFiles([]); stopListening();
  };

  return (
    <section className="flex h-full max-h-[calc(100vh-128px)] min-h-0 w-full max-w-[1220px] flex-col rounded-[34px] border border-white/75 bg-white/80 p-5 shadow-[0_28px_90px_rgba(15,23,42,0.24)] backdrop-blur-2xl sm:p-6 lg:p-7">
      <header className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-4 sm:gap-5">
          <div className="relative flex h-16 w-16 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-100 to-white shadow-[0_16px_38px_rgba(20,184,166,0.28)] sm:h-[78px] sm:w-[78px]">
            <div className="absolute inset-0 rounded-full border-4 border-cyan-100/80" />
            <Image src="/images/robot-avatar.png" alt="AI avatar" width={58} height={58} className="relative object-contain" priority />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-extrabold tracking-tight text-slate-950 sm:text-4xl">Roamora AI</h1>
              <Sparkles className="h-7 w-7 text-teal-500" />
            </div>
            <p className="mt-1 text-base font-medium text-slate-500 sm:text-lg">Your intelligent travel companion</p>
          </div>
        </div>
        <button type="button" role="switch" aria-checked={voiceOn} onClick={toggleVoice} className={`flex items-center gap-3 rounded-full border border-white/80 px-4 py-3 shadow-sm transition-all duration-300 hover:scale-[1.02] ${voiceOn ? "bg-teal-700 text-white shadow-[0_14px_32px_rgba(13,148,136,0.35)]" : "bg-white/75 text-slate-700 hover:bg-white"}`}>
          <span className={`flex h-9 w-9 items-center justify-center rounded-full ${voiceOn ? "bg-white/20" : "bg-cyan-50"}`}>{voiceOn ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}</span>
          <span className="hidden text-sm font-extrabold sm:inline">{voiceOn ? "Voice On" : "Voice Off"}</span>
          <span className={`relative h-7 w-12 rounded-full ${voiceOn ? "bg-white/30" : "bg-slate-200"}`}><span className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-md transition-all ${voiceOn ? "left-6" : "left-1"}`} /></span>
        </button>
      </header>

      <div className="mt-6 flex flex-1 flex-col justify-center gap-4 overflow-y-auto pr-1">{messages.map((m) => <ChatBubble key={m.id} message={m} />)}</div>

      <div className="mt-5 flex flex-wrap justify-center gap-3">
        {suggestions.map((s, i) => <button key={s} className={`${i ? "bg-white/80 text-slate-700 hover:bg-white" : "border border-teal-500/70 bg-white/60 text-teal-700 hover:bg-teal-50"} rounded-full px-5 py-3 text-sm font-bold shadow-sm transition sm:text-base`}>{s}</button>)}
      </div>

      <footer className="mt-5 rounded-[26px] border border-white/70 bg-white/75 p-2 shadow-[0_12px_40px_rgba(15,23,42,0.08)]">
        {!!files.length && (
          <div className="mb-2 flex flex-wrap gap-2">
            {files.map((file, i) => (
              <div key={`${file.name}-${i}`} className="flex max-w-[260px] items-center gap-2 rounded-2xl bg-teal-50 px-3 py-2 text-sm font-bold text-teal-800">
                <Paperclip className="h-4 w-4 shrink-0" /><span className="truncate">{file.name}</span>
                <button type="button" aria-label={`Remove ${file.name}`} onClick={() => setFiles((f) => f.filter((_, x) => x !== i))} className="ml-1 rounded-full p-1 text-teal-700 transition hover:bg-teal-100 hover:text-teal-950"><X className="h-4 w-4" /></button>
              </div>
            ))}
          </div>
        )}
        <div className="flex items-center gap-2.5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white text-slate-700 shadow-sm"><Plus className="h-6 w-6" /></div>
          <input ref={fileRef} type="file" multiple onChange={handleFileChange} className="hidden" />
          <button type="button" aria-label="Attach files" onClick={() => fileRef.current?.click()} className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-slate-600 transition hover:bg-white" title="Attach files"><Paperclip className="h-6 w-6" /></button>
          <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && sendMessage()} className="min-w-0 flex-1 bg-transparent px-2 text-base font-medium text-slate-700 outline-none placeholder:text-slate-500" placeholder={listening ? "Listening..." : "Ask anything about travel..."} />
          <button type="button" aria-label={listening ? "Stop listening" : "Start voice input"} onClick={toggleListening} className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl shadow-sm transition hover:scale-105 ${listening ? "bg-red-500 text-white shadow-[0_14px_32px_rgba(239,68,68,0.35)]" : "bg-white text-slate-700 hover:bg-teal-50"}`}>{listening ? <MicOff className="h-6 w-6" /> : <Mic className="h-6 w-6" />}</button>
          <button type="button" aria-label="Send message" onClick={sendMessage} className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-700 to-cyan-700 text-white shadow-[0_14px_32px_rgba(13,148,136,0.35)] transition hover:scale-105"><Send className="h-6 w-6" /></button>
        </div>
      </footer>
    </section>
  );
}

function ChatBubble({ message }: { message: ChatMessage }) {
  if (message.role === "user") return (
    <div className="flex justify-end">
      <div className="max-w-[520px] rounded-[22px] rounded-tr-md bg-gradient-to-br from-teal-700 to-cyan-700 px-6 py-4 text-white shadow-[0_14px_30px_rgba(13,148,136,0.28)]">
        {message.lines.map((line) => <p key={line} className="text-base font-bold leading-relaxed">{line}</p>)}
        <div className="mt-2 flex items-center justify-end gap-2 text-xs text-white/80"><span>{message.time}</span><CheckCheck className="h-4 w-4" /></div>
      </div>
    </div>
  );

  return (
    <div className="flex items-start gap-4">
      <BotAvatarSmall />
      <div className="max-w-[720px] rounded-[22px] rounded-tl-md bg-white px-6 py-5 shadow-[0_14px_38px_rgba(15,23,42,0.10)]">
        <div className="space-y-4">{message.lines.map((line) => <p key={line} className="text-base font-extrabold leading-relaxed text-slate-900 sm:text-lg">{line}</p>)}</div>
        <p className="mt-3 text-right text-sm font-medium text-slate-400">{message.time}</p>
      </div>
    </div>
  );
}

function BotAvatarSmall() {
  return <div className="mt-2 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-cyan-50 shadow-[0_10px_26px_rgba(20,184,166,0.22)]"><Image src="/images/robot-avatar.png" alt="AI avatar" width={38} height={38} className="object-contain" /></div>;
}