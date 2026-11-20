import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Suspense } from "react";
import Nav from "@/components/Nav";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Amtspost – understand your German letters",
  description:
    "Photograph an official German letter. Get a plain-English explanation, the real deadline, a calendar reminder and a German reply.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-stone-50 text-stone-900">
        <Suspense fallback={<div className="h-14 border-b border-stone-200 bg-white" />}>
          <Nav />
        </Suspense>
        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-stone-200 py-6 text-center text-xs text-stone-500">
          Amtspost gives information, not legal or tax advice. Always check against your original letter.
        </footer>
      </body>
    </html>
  );
}
