export type ModelKey = "base" | "travel";

export const modelOptions: Array<{ key: ModelKey; label: string; helper: string }> = [
  { key: "base", label: "Base LLaMA", helper: "General reasoning model" },
  { key: "travel", label: "Fine-Tuned Travel", helper: "Optimized travel planner" },
];

export const assistantScrollbarStyle = `
  .assistant-scroll {
    scrollbar-width: thin;
    scrollbar-color: #6366f1 transparent;
  }
  .assistant-scroll::-webkit-scrollbar { width: 8px; }
  .assistant-scroll::-webkit-scrollbar-track { background: transparent; }
  .assistant-scroll::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #3b82f6, #8b5cf6);
    border-radius: 999px;
    box-shadow: 0 0 14px rgba(99, 102, 241, 0.55);
  }
`;
