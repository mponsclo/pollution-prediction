import type { Metadata } from "next";
import { Inter_Tight, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const interTight = Inter_Tight({
  variable: "--font-inter-tight",
  subsets: ["latin"],
  display: "swap",
});

const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Seoul Air Quality",
    template: "%s · Seoul Air Quality",
  },
  description:
    "Air quality monitoring and forecasting for 25 Seoul stations — visualization-as-code dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${interTight.variable} ${jetBrainsMono.variable}`}>
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
