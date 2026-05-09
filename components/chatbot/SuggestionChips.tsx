import { CalendarDays, Utensils } from "lucide-react";

const SUGGESTIONS = [
  { Icon: CalendarDays, label: "1 Day trip to Berlin" },
  { Icon: CalendarDays, label: "3 day trip to Munich with faster pace" },
  { Icon: Utensils, label: "5 day trip to Stuttgart with more food experiences" },
];

interface SuggestionChipsProps {
  onSelect: (label: string) => void;
  disabled: boolean;
}

export function SuggestionChips({ onSelect, disabled }: SuggestionChipsProps) {
  return (
    <div className="mt-4 flex flex-wrap justify-center gap-2 sm:gap-3">
      {SUGGESTIONS.map(({ Icon, label }) => (
        <button
          key={label}
          onClick={() => onSelect(label)}
          disabled={disabled}
          className="flex items-center gap-1.5 rounded-full border border-teal-500/70 bg-white/60 px-3 py-2 text-xs font-semibold text-teal-700 shadow-sm transition hover:bg-white/90 disabled:opacity-50 sm:px-4 sm:py-2.5 sm:text-sm"
        >
          <Icon className="h-4 w-4" />
          {label}
        </button>
      ))}
    </div>
  );
}
