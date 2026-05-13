import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "FinSpace | Pénzügyeid egy helyen",
  description: "Személyes és üzleti pénzügyi asszisztens Ádámnak és párjának.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "FinSpace",
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
    <html lang="hu">
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
