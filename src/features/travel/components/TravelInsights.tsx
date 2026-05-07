import { useState } from "react";
import { CloudSun, Hotel, ReceiptText, TrainFront, WalletCards } from "lucide-react";

const insights = [
  { icon: CloudSun, label: "Weather", title: "Paris, FR - 18C", detail: "Partly cloudy", action: "Hourly forecast opened", tone: "from-orange-400 to-amber-300" },
  { icon: ReceiptText, label: "Budget", title: "EUR 420 / EUR 600", detail: "Daily budget used", action: "Budget categories expanded", tone: "from-emerald-500 to-teal-400" },
  { icon: Hotel, label: "Hotel", title: "Hotel Relais Montmartre", detail: "EUR 126/night - 4.7 rating", action: "Hotel shortlist opened", tone: "from-violet-500 to-fuchsia-400" },
  { icon: TrainFront, label: "Transport", title: "Metro Day Pass", detail: "EUR 7.50 - Unlimited rides", action: "Transport route opened", tone: "from-blue-500 to-indigo-400" },
];

export function TravelInsights() {
  const [activeInsight, setActiveInsight] = useState(insights[1]);

  return (
    <div className="overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_18px_45px_rgba(15,23,42,.1)]">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <div className="mb-1 text-xs font-semibold text-blue-700">{activeInsight.action}</div>
          <h2 className="text-lg font-bold text-slate-950">Travel Insights</h2>
        </div>
        <WalletCards className="h-5 w-5 text-slate-400" />
      </div>
      <div className="grid grid-cols-2 gap-3 p-5">
        {insights.map((item) => {
          const Icon = item.icon;
          const isActive = activeInsight.label === item.label;
          return (
            <button
              key={item.label}
              onClick={() => setActiveInsight(item)}
              className={`rounded-2xl border p-3 text-left transition hover:bg-white hover:shadow-md ${
                isActive ? "border-blue-200 bg-blue-50" : "border-slate-100 bg-slate-50"
              }`}
            >
              <div className="mb-3 flex items-center justify-between">
                <div className={`flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br ${item.tone} text-white shadow-lg`}>
                  <Icon className="h-4 w-4" />
                </div>
                <span className="text-xs font-semibold text-slate-400">{item.label}</span>
              </div>
              <h3 className="text-sm font-bold text-slate-950">{item.title}</h3>
              <p className="mt-1 text-xs text-slate-500">{item.detail}</p>
              {item.label === "Budget" && (
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white">
                  <div className="h-full w-[70%] rounded-full bg-gradient-to-r from-emerald-500 to-teal-400" />
                </div>
              )}
            </button>
          );
        })}
        <div className="col-span-2 rounded-2xl border border-orange-100 bg-orange-50 p-3 text-sm text-orange-800">
          Local cost tip: Lunch menus near Montmartre are usually 18-24 EUR, while central tourist zones average 28-34 EUR.
        </div>
      </div>
    </div>
  );
}
