import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import Script from "next/script";
import { Analytics } from "@vercel/analytics/next";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "StoryTúrák - Mozogj észrevétlenül, játssz közben",
  description: "Napi pár perc sétával akár havi 12 000 kalóriát is elégethetsz – és közben a karaktered fejlődik a játékban.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="hu" className={`${inter.variable} ${outfit.variable}`}>
      <body className="antialiased bg-background-dark text-foreground">
        {children}
        <Analytics />
        <Script
          src="https://tally.so/widgets/embed.js"
          strategy="lazyOnload"
        />
      </body>
    </html>
  );
}
