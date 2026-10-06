import type { Metadata, Viewport } from "next";
import Link from "next/link";
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
        <header className="border-b border-ink/10 bg-paper">
          <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-5" aria-label="Main navigation">
            <Link href="/" className="text-lg font-semibold tracking-tight text-brand focus:outline-none focus:ring-2 focus:ring-brand">
              NotesNest
            </Link>
            <Link href="/faculty" className="min-h-11 px-2 py-2 text-sm font-medium text-ink/70 hover:text-brand focus:outline-none focus:ring-2 focus:ring-brand">
              Faculty
            </Link>
            <Link href="/advice" className="min-h-11 px-2 py-2 text-sm font-medium text-ink/70 hover:text-brand focus:outline-none focus:ring-2 focus:ring-brand">
              Advice
            </Link>
          </nav>
        </header>
        <main className="mx-auto min-h-[calc(100vh-145px)] max-w-5xl px-4 py-8 sm:py-12">{children}</main>
        <footer className="border-t border-ink/10">
          <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-ink/60">
            NotesNest · A simpler way to find your course materials.
          </div>
        </footer>
      </body>
    </html>
  );
}
