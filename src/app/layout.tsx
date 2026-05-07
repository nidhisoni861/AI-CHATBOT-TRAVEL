import type { Metadata } from "next";
import "../styles/index.css";

export const metadata: Metadata = {
  title: "AI Travel Assistance",
  description: "AI generated global travel planning console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
