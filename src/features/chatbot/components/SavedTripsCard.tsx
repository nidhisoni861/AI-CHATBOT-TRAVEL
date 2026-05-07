"use client";
import React from "react";

function TripCard({ title, date, days, people, status }: { title: string; date: string; days: string; people: string; status: string }) {
  return (
    <div className="p-3 rounded-2xl bg-white/5 border border-white/6 hover:scale-[1.02] transition-transform flex items-center gap-3">
      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-indigo-500 to-pink-400 flex items-center justify-center text-white font-bold">{title.charAt(0)}</div>
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <div className="font-medium">{title}</div>
          <div className={`text-xs px-2 py-1 rounded-full ${status === 'Upcoming' ? 'bg-indigo-600 text-white' : status === 'Completed' ? 'bg-emerald-500 text-white' : 'bg-zinc-600 text-white'}`}>{status}</div>
        </div>
        <div className="text-xs text-zinc-400">{date} · {days} · {people}</div>
      </div>
      <div className="flex flex-col items-end gap-2">
        <button className="p-2 rounded-full bg-white/5">⋯</button>
        <button className="p-2 rounded-full bg-white/5">🔖</button>
      </div>
    </div>
  );
}

export default function SavedTripsCard() {
  return (
    <div className="rounded-2xl bg-white/60 dark:bg-zinc-900/60 backdrop-blur-md border border-white/6 p-4 shadow-2xl flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">Saved Trips</h3>
        <button className="px-3 py-1 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-500 text-white">New Trip</button>
      </div>

      <div className="flex flex-col gap-3">
        <TripCard title="Paris Getaway" date="Jun 12 – Jun 16, 2025" days="4 Days" people="2 People" status="Upcoming" />
        <TripCard title="Tokyo Explorer" date="Jul 03 – Jul 10, 2025" days="7 Days" people="1 Person" status="Upcoming" />
        <TripCard title="Barcelona Escape" date="May 20 – May 24, 2025" days="5 Days" people="2 People" status="Completed" />
        <TripCard title="Bali Retreat" date="Aug 15 – Aug 22, 2025" days="8 Days" people="2 People" status="Saved" />
      </div>

      <div className="mt-4">
        <button className="w-full px-4 py-2 rounded-lg bg-white/5 hover:bg-white/7">View All Trips</button>
      </div>
    </div>
  );
}
