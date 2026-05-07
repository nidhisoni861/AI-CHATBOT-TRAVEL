import { useState } from "react";
import { BarChart3, Bot, ChevronLeft, Compass, Globe2, Map, MapPin, Plane, Settings, Sparkles, X } from "lucide-react";

interface LeftSidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
  pageLanguage: string;
  onLanguageChange: (language: string) => void;
}

export function LeftSidebar({ activeSection, onSectionChange, pageLanguage, onLanguageChange }: LeftSidebarProps) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const sections = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "trip-planner", label: "Trip Planner", icon: Compass },
    { id: "map-route", label: "Map & Route", icon: MapPin },
    { id: "translation", label: "Live Translation", icon: Globe2 },
    { id: "saved-trips", label: "Saved Trips", icon: Plane },
    { id: "insights", label: "Insights", icon: Sparkles },
  ];

  return (
    <aside className="sticky top-0 flex h-screen w-[292px] flex-col border-r border-white/10 bg-[radial-gradient(circle_at_20%_0%,rgba(59,130,246,.3),transparent_32%),linear-gradient(180deg,#07111f_0%,#0f172a_48%,#08111f_100%)] text-white shadow-2xl">
      <div className="border-b border-white/10 p-6">
        <div className="mb-2 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-violet-500 shadow-lg shadow-blue-500/30">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-base font-bold">AI Travel Assistant</h1>
            <p className="mt-0.5 text-[11px] leading-4 text-slate-400">Fine-Tuned Multilingual Travel Planner</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {sections.map((section) => {
          const Icon = section.icon;
          const target = section.id === "insights" ? "saved-trips" : section.id;
          const isActive = activeSection === section.id || (section.id === "insights" && activeSection === "saved-trips");
          return (
            <button
              key={section.id}
              onClick={() => onSectionChange(target)}
              className={`group flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-all ${
                isActive
                  ? "border border-blue-400/30 bg-blue-500/15 text-white shadow-lg shadow-blue-500/10"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className={`h-5 w-5 ${isActive ? "text-blue-300" : "text-slate-500 group-hover:text-slate-300"}`} />
              <span className="text-sm font-medium">{section.label}</span>
            </button>
          );
        })}
      </nav>

      

      {settingsOpen && (
        <div className="absolute bottom-20 left-4 right-4 z-50 rounded-2xl border border-white/10 bg-slate-950 p-4 shadow-2xl">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-blue-300">Page language</div>
              <h3 className="text-sm font-bold text-white">Settings</h3>
            </div>
            <button onClick={() => setSettingsOpen(false)} className="rounded-lg p-1 text-slate-400 hover:bg-white/10">
              <X className="h-4 w-4" />
            </button>
          </div>
          <select
            value={pageLanguage}
            onChange={(event) => onLanguageChange(event.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/10 px-3 py-2.5 text-sm font-semibold text-white outline-none"
          >
            {["English", "French", "German", "Spanish"].map((language) => (
              <option key={language} className="text-slate-900">{language}</option>
            ))}
          </select>
          <div className="mt-3 rounded-xl bg-emerald-400/10 px-3 py-2 text-xs text-emerald-200">
            Dashboard labels update immediately. Assistant and translation language controls remain independent.
          </div>
        </div>
      )}
    </aside>
  );
}
