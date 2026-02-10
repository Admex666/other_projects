import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Odor Finium | Budapest",
  description: "Odor Finium creates limited scent objects inspired by places. Budapest is the first.",
  openGraph: {
    title: "Odor Finium | Budapest",
    description: "Not a souvenir. A memory you take home.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${inter.variable} antialiased`}>
      <head>
        <Script
          defer
          data-domain="odorfinium.com"
          src="https://plausible.io/js/script.js"
          strategy="afterInteractive"
        />
      </head>
      <body className="bg-background text-foreground font-sans selection:bg-neutral-200 selection:text-black">
        {children}
      </body>
    </html>
  );
}
