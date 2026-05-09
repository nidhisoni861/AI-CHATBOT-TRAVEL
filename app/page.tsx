import RouteCard from "@/src/features/chatbot/components/RouteCard";
import ChatBotPanel from "@/src/features/chatbot/components/ChatBotPanel";
import SavedTripsPanel from "@/src/features/chatbot/components/SavedTripsPanel";

export default function HomePage() {
  return (
    <main className="relative min-h-screen overflow-x-hidden bg-slate-950 text-slate-950 xl:h-screen xl:overflow-hidden">
      {/* Background image */}
      <div
        className="absolute inset-0 z-0 bg-cover bg-center bg-no-repeat"
        style={{
          backgroundImage: "url('/images/travel-bg.png')",
        }}
      />

      {/* Soft overlay */}
      <div className="absolute inset-0 z-[1] bg-gradient-to-r from-cyan-100/20 via-white/15 to-rose-200/20" />

      {/* Decorative animation layer */}
      <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden">
        <div className="animate-float-slow absolute -left-16 top-10 h-72 w-72 rounded-full bg-pink-200/30 blur-3xl" />
        <div className="animate-float-medium absolute right-12 top-12 h-80 w-80 rounded-full bg-cyan-300/25 blur-3xl" />
        <div className="animate-float-reverse absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-white/20 blur-3xl" />

        <div className="absolute left-[4%] top-[8%] h-px w-[32rem] rotate-[14deg] bg-white/45" />
        <div className="absolute right-[7%] top-[14%] h-px w-[28rem] -rotate-[18deg] bg-yellow-100/35" />
        <div className="absolute bottom-[10%] right-[2%] h-px w-[38rem] -rotate-[8deg] bg-white/25" />

        <div className="absolute left-4 top-4 grid grid-cols-4 gap-4 opacity-40">
          {Array.from({ length: 28 }).map((_, index) => (
            <span
              key={index}
              className="h-1.5 w-1.5 rounded-full bg-white/70"
            />
          ))}
        </div>
      </div>

      {/* Main UI */}
      <section className="relative z-10 mx-auto grid min-h-screen w-full max-w-[1480px] grid-cols-1 items-center gap-5 px-5 py-6 sm:px-7 lg:px-8 xl:h-screen xl:min-h-0 xl:grid-cols-[320px_minmax(600px,760px)_320px] xl:gap-6 xl:py-5 2xl:max-w-[1540px] 2xl:grid-cols-[340px_minmax(660px,800px)_340px] 2xl:gap-8">
        <div className="order-2 xl:order-1">
          <RouteCard />
        </div>

        <div className="order-1 xl:order-2">
          <ChatBotPanel />
        </div>

        <div className="order-3 xl:order-3">
          <SavedTripsPanel />
        </div>
      </section>
    </main>
  );
}