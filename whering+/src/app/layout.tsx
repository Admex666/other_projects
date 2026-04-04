import type { Metadata, Viewport } from "next";
import { Inter, Manrope } from "next/font/google";
import "./globals.css";
import { PWARegister } from "@/components/PWARegister";

const inter = Inter({
  variable: "--font-family-body",
  subsets: ["latin"],
});

const manrope = Manrope({
  variable: "--font-family-display",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "The Digital Atelier | Your Wardrobe, Curated",
  description: "A premium, AI-powered wardrobe management and outfit validation app designed for confidence and clarity.",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Digital Atelier",
  },
};

export const viewport: Viewport = {
  themeColor: "#fbf9f5", /* surface color */
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
    <html lang="en" className={`${inter.variable} ${manrope.variable}`} suppressHydrationWarning>
      <body suppressHydrationWarning>
        <PWARegister />
        {children}
      </body>
    </html>
  );
}
