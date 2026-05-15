import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";
import Navigation from "@/components/Navigation";

export const metadata: Metadata = {
  title: "FinSpace | Pénzügyeid egy helyen",
  description: "Személyes és üzleti pénzügyi asszisztens Ádámnak és párjának.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "FinSpace",
  },
  icons: {
    apple: "/icons/icon-192x192.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#0F0F14",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hu" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Providers>
          {children}
          <Navigation />
        </Providers>
      </body>
    </html>
  );
}
