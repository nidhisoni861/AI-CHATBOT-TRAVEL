import { useEffect, useRef, useState } from "react";
import { Bot, Brain, ChevronDown, Globe, Maximize2, Mic, Minus, Send, Sparkles, X } from "lucide-react";
import { assistantScrollbarStyle, modelOptions, type ModelKey } from "../data/assistant-options";
import {
  sendChatMessage,
  type DashboardPayload,
  type ModelMode,
} from "../../../lib/api";

const LANGUAGE_OPTIONS = [
  { code: "English", label: "EN", full: "English" },
  { code: "German", label: "DE", full: "Deutsch" },
  { code: "French", label: "FR", full: "Français" },
  { code: "Spanish", label: "ES", full: "Español" },
  { code: "Italian", label: "IT", full: "Italiano" },
];

interface FloatingAssistantProps {
  isOpen: boolean;
  onToggle: () => void;
  onSetBudget: (budget: number) => void;
  onOptimizePrices: () => void;
  onFocusStop: (stopId: number) => void;
  onDashboardUpdate?: (payload: DashboardPayload) => void;
}

export function FloatingAssistant({ isOpen, onToggle, onSetBudget, onOptimizePrices, onFocusStop, onDashboardUpdate }: FloatingAssistantProps) {
  const [selectedModel, setSelectedModel] = useState<ModelKey>("travel");
  const [selectedLanguage, setSelectedLanguage] = useState("English");
  const [showDropdown, setShowDropdown] = useState(false);
  const [showLangDropdown, setShowLangDropdown] = useState(false);
  const [showLatest, setShowLatest] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [messages, setMessages] = useState<Array<{ role: "assistant" | "user"; text: string }>>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const sessionId = useRef(`session_${Math.random().toString(36).slice(2)}`);
  const scrollRef = useRef<HTMLDivElement>(null);
  const latestRef = useRef<HTMLDivElement>(null);
  const selectedModelMeta = modelOptions.find((model) => model.key === selectedModel) ?? modelOptions[1];
  const selectedLangMeta = LANGUAGE_OPTIONS.find((l) => l.code === selectedLanguage) ?? LANGUAGE_OPTIONS[0];

  const scrollToLatest = () => latestRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });

  useEffect(() => {
    requestAnimationFrame(scrollToLatest);
  }, [messages]);

  const handleScroll = () => {
    const node = scrollRef.current;
    if (!node) return;
    setShowLatest(node.scrollHeight - node.scrollTop - node.clientHeight > 80);
  };

  const SUGGESTION_CHIPS = [
    "Plan a 3-day trip to Barcelona",
    "What's the weather like in Tokyo in April?",
    "Find budget hotels in Rome under EUR 80/night",
    "Create a weekend itinerary for Amsterdam",
  ];

  const MODEL_MODE_MAP: Record<ModelKey, ModelMode> = {
    travel: "fine_tuned",
    base: "base",
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    setIsLoading(true);
    setMessages((items) => [...items, { role: "user", text }]);

    try {
      const data = await sendChatMessage({
        session_id: sessionId.current,
        message: text,
        model_mode: MODEL_MODE_MAP[selectedModel],
        language: selectedLanguage,
      });
      const reply = data.assistant_message || "No response from model.";
      setMessages((items) => [...items, { role: "assistant", text: reply }]);
      if (data.dashboard_payload?.schema_version === "travel_dashboard_v1") {
        onDashboardUpdate?.(data.dashboard_payload);
        // Execute dashboard_actions returned by the model
        for (const act of data.dashboard_payload.dashboard_actions ?? []) {
          if (act.action === "set_budget") {
            const val = parseFloat(act.target);
            if (!isNaN(val)) onSetBudget(val);
          } else if (act.action === "optimize_prices") {
            onOptimizePrices();
          } else if (act.action === "focus_map_stop" || act.action === "focus_stop") {
            const stopNum = parseInt(act.target, 10);
            if (!isNaN(stopNum)) onFocusStop(stopNum);
          }
        }
      }
    } catch (err) {
      setMessages((items) => [
        ...items,
        { role: "assistant", text: "Could not reach the backend. Make sure the FastAPI server is running on port 8000." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const assistantWindowClassName = isMaximized
  ? "fixed inset-4 z-[9999] isolate flex flex-col overflow-hidden rounded-[26px] border border-white/80 bg-white shadow-[0_32px_90px_rgba(15,23,42,.28),0_0_42px_rgba(99,102,241,.25)]"
  : "fixed bottom-6 right-6 z-[9999] isolate flex h-[min(820px,calc(100vh-48px))] w-[min(470px,calc(100vw-48px))] flex-col overflow-hidden rounded-[26px] border border-white/80 bg-white shadow-[0_32px_90px_rgba(15,23,42,.28),0_0_42px_rgba(99,102,241,.25)]";

  if (!isOpen) {
    return (
      <button
  onClick={onToggle}
  className="fixed bottom-6 right-6 z-[9999] flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 via-indigo-500 to-violet-500 text-white shadow-2xl shadow-blue-500/40 transition hover:scale-105"
>
        <Bot className="h-8 w-8" />
        <span className="absolute -right-0.5 -top-0.5 h-4 w-4 rounded-full border-2 border-white bg-emerald-400 shadow-[0_0_16px_rgba(52,211,153,.9)]" />
      </button>
    );
  }

  return (
    <>
     {isMaximized && (
  <div
    className="fixed inset-0 z-[9998] bg-slate-950/60 backdrop-blur-sm"
    onClick={() => setIsMaximized(false)}
  />
)}
      <section className={assistantWindowClassName}>
        <header className="relative rounded-t-[26px] border-b border-slate-100 bg-[linear-gradient(135deg,#0f172a,#111827_56%,#172554)] px-4 py-3 text-white">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/15">
                <Sparkles className="h-5 w-5 text-blue-200" />
              </div>
              <div className="min-w-0">
                <h2 className="text-sm font-bold">AI Assistant</h2>
                <div className="mt-0.5 flex items-center gap-1.5 text-[11px] text-slate-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" />
                  Ready to plan worldwide
                </div>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-1.5">
              {/* Language picker */}
              <div className="relative z-50">
                <button onClick={() => { setShowLangDropdown((o) => !o); setShowDropdown(false); }} className="flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/10 px-2.5 py-2 text-xs font-semibold text-white hover:bg-white/15">
                  <Globe className="h-3.5 w-3.5" />
                  {selectedLangMeta.label}
                </button>
                {showLangDropdown && (
                  <div className="absolute right-0 top-11 z-[70] w-40 rounded-2xl border border-slate-200 bg-white p-1 text-slate-900 shadow-2xl">
                    {LANGUAGE_OPTIONS.map((lang) => (
                      <button key={lang.code} onClick={() => { setSelectedLanguage(lang.code); setShowLangDropdown(false); }} className={`flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm transition ${selectedLanguage === lang.code ? "bg-blue-50 font-bold text-blue-700" : "hover:bg-slate-50"}`}>
                        <span className="w-6 text-xs font-bold text-slate-400">{lang.label}</span>
                        {lang.full}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {/* Model picker */}
              <div className="relative z-50">
                <button onClick={() => { setShowDropdown((open) => !open); setShowLangDropdown(false); }} className="flex min-w-[150px] items-center justify-between gap-2 rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-xs font-semibold text-white hover:bg-white/15">
                  <span className="flex items-center gap-2">
                    {selectedModel === "travel" ? <Sparkles className="h-3.5 w-3.5 text-blue-200" /> : <Brain className="h-3.5 w-3.5" />}
                    {selectedModelMeta.label}
                  </span>
                  <ChevronDown className="h-3.5 w-3.5" />
                </button>
                {showDropdown && (
                  <div className="absolute right-0 top-11 z-[70] w-64 rounded-2xl border border-slate-200 bg-white p-1 text-slate-900 shadow-2xl">
                    {modelOptions.map((model) => {
                      const Icon = model.key === "travel" ? Sparkles : Brain;
                      const isSelected = selectedModel === model.key;
                      return (
                        <button key={model.key} onClick={() => { setSelectedModel(model.key); setShowDropdown(false); }} className={`flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition ${isSelected ? "bg-blue-50 text-blue-700" : "hover:bg-slate-50"}`}>
                          <Icon className="mt-0.5 h-4 w-4" />
                          <span>
                            <span className="block text-sm font-bold">{model.label}</span>
                            <span className="block text-xs text-slate-500">{model.helper}</span>
                          </span>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
              <button onClick={onToggle} title="Minimize assistant" className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-300 hover:bg-white/10">
                <Minus className="h-4 w-4" />
              </button>
              <button onClick={() => setIsMaximized((value) => !value)} title={isMaximized ? "Restore assistant" : "Maximize assistant"} className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-300 hover:bg-white/10">
                <Maximize2 className="h-4 w-4" />
              </button>
              <button onClick={onToggle} className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-300 hover:bg-rose-500/20 hover:text-rose-200">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </header>

        <div className="relative min-h-0 flex-1 overflow-hidden bg-gradient-to-b from-slate-50 to-white">
          <div ref={scrollRef} onScroll={handleScroll} className="assistant-scroll h-full overflow-y-auto">
            {messages.length === 0 ? (
              <div className="flex min-h-full flex-col justify-start p-5 pt-12">
                <div className="rounded-3xl border border-blue-100 bg-white p-5 text-center shadow-sm">
                  <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-violet-500 text-white">
                    <Bot className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-950">Where should we go?</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    Ask for any city or country. I can ask follow-up questions, adjust budgets, optimize prices, and focus dashboard widgets.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-3 p-5">
                {messages.map((message, index) => (
                  <div key={index} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[86%] rounded-3xl px-4 py-3 text-sm leading-6 shadow-sm ${message.role === "user" ? "rounded-tr-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white" : "rounded-tl-lg border border-slate-100 bg-white text-slate-700"}`}>
                      {message.text}
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="rounded-3xl rounded-tl-lg border border-slate-100 bg-white px-4 py-3 text-sm text-slate-400 shadow-sm">
                      <span className="inline-flex gap-1">
                        <span className="animate-bounce" style={{ animationDelay: "0ms" }}>●</span>
                        <span className="animate-bounce" style={{ animationDelay: "150ms" }}>●</span>
                        <span className="animate-bounce" style={{ animationDelay: "300ms" }}>●</span>
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
            <div ref={latestRef} className="h-4" />
          </div>

          {showLatest && (
            <button onClick={scrollToLatest} className="absolute bottom-3 left-1/2 z-30 -translate-x-1/2 rounded-full bg-slate-950 px-3 py-1.5 text-xs font-semibold text-white shadow-xl">
              Scroll to latest
            </button>
          )}
        </div>

        <footer className="rounded-b-[26px] border-t border-slate-100 bg-white p-4">
          {messages.length === 0 && (
            <div className="mb-2 flex flex-wrap gap-1.5">
              {SUGGESTION_CHIPS.map((chip) => (
                <button
                  key={chip}
                  onClick={() => { setInput(chip); }}
                  className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                >
                  {chip}
                </button>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2">
            <input value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => event.key === "Enter" && !isLoading && sendMessage()} disabled={isLoading} className="min-w-0 flex-1 bg-transparent px-2 text-sm outline-none disabled:opacity-50" placeholder="Ask the assistant to plan any destination..." />
            <button className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-slate-500 shadow-sm"><Mic className="h-4 w-4" /></button>
            <button onClick={sendMessage} disabled={isLoading} className={`flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25 transition ${isLoading ? "cursor-not-allowed opacity-50" : ""}`}><Send className="h-4 w-4" /></button>
          </div>
        </footer>
      </section>

      <style>{assistantScrollbarStyle}</style>
    </>
  );
}
