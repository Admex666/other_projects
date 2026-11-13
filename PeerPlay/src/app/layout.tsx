import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import { Toaster } from 'react-hot-toast';
import "./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: 'swap',
});

export const metadata: Metadata = {
  title: "PeerPlay · The Trading Game & Organizational Diagnostics",
  description: "Behavioral Simulation-Based Organizational Diagnostics Platform (Stripe Enterprise Standard)",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hu" className={`${plusJakartaSans.variable} ${jetbrainsMono.variable}`}>
      <body
        className="font-sans bg-slate-50 text-slate-900 antialiased min-h-screen selection:bg-blue-100 selection:text-blue-900"
        suppressHydrationWarning
      >
        <Toaster
          position="top-right"
          toastOptions={{
            className: 'text-sm font-medium border border-slate-200 bg-white shadow-md text-slate-800 rounded-lg',
            duration: 3500,
          }}
        />
        {children}
      </body>
    </html>
  );
}
