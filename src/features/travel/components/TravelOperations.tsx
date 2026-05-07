// import { useMemo } from "react";
// import { Landmark, Luggage, Ticket } from "lucide-react";

// const bookingItems = [
//   { label: "Eiffel Tower summit ticket", type: "Ticket" },
//   { label: "Louvre timed entry", type: "Ticket" },
//   { label: "Seine river cruise", type: "Experience" },
//   { label: "Metro day pass", type: "Transport" },
// ];

// const highlights = [
//   {
//     title: "Eiffel Tower",
//     detail: "Best morning viewpoint",
//     image: "https://images.unsplash.com/photo-1543349689-9a4d426bee8e?auto=format&fit=crop&w=600&q=80",
//   },
//   {
//     title: "Louvre Museum",
//     detail: "Culture route and timed entry",
//     image: "https://images.unsplash.com/photo-1565099824688-e93eb20fe622?auto=format&fit=crop&w=600&q=80",
//   },
//   {
//     title: "Montmartre",
//     detail: "Sunset, artists, local food",
//     image: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=600&q=80",
//   },
// ];

// interface TravelOperationsProps {
//   bookingPrices: Record<string, number>;
// }

// export function TravelOperations({ bookingPrices }: TravelOperationsProps) {
//   const cartTotal = useMemo(
//     () => bookingItems.reduce((total, item) => total + bookingPrices[item.label], 0),
//     [bookingPrices],
//   );

//   return (
//     <div className="space-y-5">
//       <div className="rounded-2xl border border-white/70 bg-white p-5 shadow-[0_18px_45px_rgba(15,23,42,.08)]">
//         <div className="mb-3 flex items-center justify-between">
//           <div>
//             <div className="text-xs font-semibold text-blue-700">Purchasing</div>
//             <h2 className="text-base font-bold text-slate-950">Bookings</h2>
//           </div>
//           <Ticket className="h-5 w-5 text-blue-600" />
//         </div>
//         <div className="space-y-2">
//           {bookingItems.map((item) => {
//             return (
//               <div
//                 key={item.label}
//                 className="flex w-full items-center justify-between gap-4 rounded-xl border border-blue-100 bg-blue-50 p-3 text-left text-sm transition"
//               >
//                 <span className="min-w-0">
//                   <span className="block font-bold text-slate-900">{item.label}</span>
//                   <span className="text-xs text-slate-500">{item.type}</span>
//                 </span>
//                 <span className="shrink-0 font-bold text-slate-900">EUR {bookingPrices[item.label]}</span>
//               </div>
//             );
//           })}
//         </div>
//         <div className="mt-3 rounded-xl bg-slate-950 px-3 py-2 text-sm font-bold text-white">
//           AI-estimated cart total: EUR {cartTotal}
//         </div>
//       </div>

//       <div className="rounded-2xl border border-white/70 bg-white p-5 shadow-[0_18px_45px_rgba(15,23,42,.08)]">
//         <div className="mb-3 flex items-center gap-2">
//           <Landmark className="h-5 w-5 text-orange-600" />
//           <h2 className="text-base font-bold text-slate-950">Main city highlights</h2>
//           <span className="rounded-full bg-orange-50 px-2.5 py-1 text-xs font-semibold text-orange-700">Unsplash destination imagery</span>
//         </div>
//         <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
//           {highlights.map((highlight) => (
//             <div key={highlight.title} className="overflow-hidden rounded-2xl border border-slate-100 bg-slate-50">
//               <img src={highlight.image} alt={highlight.title} className="h-24 w-full object-cover" />
//               <div className="p-3">
//                 <div className="flex items-center gap-2 text-sm font-bold text-slate-950">
//                   <Luggage className="h-4 w-4 text-blue-600" />
//                   {highlight.title}
//                 </div>
//                 <p className="mt-1 text-xs text-slate-500">{highlight.detail}</p>
//               </div>
//             </div>
//           ))}
//         </div>
//       </div>
//     </div>
//   );
// }
