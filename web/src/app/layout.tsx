import type { Metadata } from "next";
import { IBM_Plex_Mono, Instrument_Sans } from "next/font/google";
import type { ReactNode } from "react";

import { AppShell } from "@/components/app-shell";
import "./globals.css";

const body = Instrument_Sans({ subsets: ["latin"], variable: "--font-body" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: { default: "FraudLens Bharat", template: "%s · FraudLens Bharat" },
  description: "Explainable local cyber-fraud triage for Indian messages and screenshots.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" className={`${body.variable} ${mono.variable}`}>
      <body><AppShell>{children}</AppShell></body>
    </html>
  );
}
