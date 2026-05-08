"use client";
import React from "react";

function TripThumbnail({ variant }: { variant: string }) {
  const bg = variant === "paris" ? "from-pink-300 to-indigo-400" : variant === "tokyo" ? "from-indigo-400 to-sky-400" : variant === "barcelona" ? "from-yellow-300 to-orange-400" : "from-emerald-300 to-cyan-400";
  return <div className={`w-16 h-12 rounded-lg bg-gradient-to-br ${bg} flex items-center justify-center text-white font-bold`}>📷</div>;
}

function TripItem({ title, date, days, people, status, variant }: { title: string; date: string; days: string; people: string; status: string; variant: string }) {
  return (
    <div className="p-3 rounded-2xl bg-white/50 border border-white/60 flex items-center gap-3 hover:-translate-y-1 transition-transform">
      <TripThumbnail variant={variant} />
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <div className="font-medium">{title}</div>
          <div className={`text-xs px-2 py-1 rounded-full ${status === 'Upcoming' ? 'bg-indigo-600 text-white' : status === 'Completed' ? 'bg-emerald-500 text-white' : 'bg-zinc-600 text-white'}`}>{status}</div>
        </div>
        <div className="text-xs text-slate-600">{date} · {days} · {people}</div>
      </div>
      <div className="flex flex-col gap-2">
        <button className="p-2 rounded-full bg-white/5">⋯</button>
        <button className="p-2 rounded-full bg-white/5">🔖</button>
      </div>
    </div>
  );
}

export default function SavedTripsCard() {
  return (
    <div className="rounded-2xl bg-white/45 backdrop-blur-2xl border border-white/60 p-4 shadow-[0_20px_60px_rgba(124,58,237,0.08)]">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-pink-400 flex items-center justify-center text-white">🧳</div>
          <div className="font-semibold">Saved Trips</div>
        </div>
        <button className="px-3 py-1 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-500 text-white">+ New Trip</button>
      </div>

      <div className="flex flex-col gap-3">
        <TripItem title="Paris Getaway" date="Jun 12 – Jun 16, 2025" days="4d" people="2p" status="Upcoming" variant="paris" />
        <TripItem title="Tokyo Explorer" date="Jul 03 – Jul 10, 2025" days="7d" people="1p" status="Upcoming" variant="tokyo" />
        <TripItem title="Barcelona Escape" date="May 20 – May 24, 2025" days="5d" people="2p" status="Completed" variant="barcelona" />
        <TripItem title="Bali Retreat" date="Aug 15 – Aug 22, 2025" days="8d" people="2p" status="Saved" variant="bali" />
      </div>

      <div className="mt-4">
        <button className="w-full px-4 py-2 rounded-lg bg-white/5 hover:bg-white/7">View All Trips</button>
      </div>
    </div>
  );
}
