import type { Metadata, Viewport } from "next";
import { Navigation } from "@/components/Navigation";
import { RouteFocus } from "@/components/RouteFocus";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NotesNest",
  description: "PYQs, notes, faculty info and advice for BSc students.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans">
        <a
          href="#main-content"
          className="sr-only z-50 rounded-md bg-paper px-4 py-3 text-sm font-medium text-ink focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:ring-2 focus:ring-brand"
        >
          Skip to main content
        </a>
        <header className="border-b border-ink/20 bg-paper">
          <Navigation />
        </header>
        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto min-h-[calc(100vh-145px)] max-w-5xl px-4 py-8 focus:outline-none sm:py-12"
        >
          <RouteFocus />
          {children}
        </main>
        <footer className="border-t border-ink/20">
          <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-ink/70">
            NotesNest · A simpler way to find your course materials.
          </div>
        </footer>
        <Analytics />
      </body>
    </html>
  );
}