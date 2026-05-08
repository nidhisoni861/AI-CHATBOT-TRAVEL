import "./globals.css";
import type { Metadata } from "next";
import { PropsWithChildren } from "react";

export const metadata: Metadata = {
  title: "WanderAI",
  description: "AI Travel Assistant",
};

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-screen bg-[linear-gradient(180deg,#eef2ff_0%,#fff1f8_100%)] text-slate-900">
        {children}
      </body>
    </html>
  );
}
