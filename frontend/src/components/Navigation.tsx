"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Navigation() {
  const pathname = usePathname();
  const links = [
    { href: "/faculty", label: "Faculty" },
    { href: "/advice", label: "Advice" },
  ];

  return (
    <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-5" aria-label="Main navigation">
      <Link href="/" className="text-lg font-semibold tracking-tight text-brand focus:outline-none focus:ring-2 focus:ring-brand">
        NotesNest
      </Link>
      <div className="flex items-center gap-1">
        {links.map((link) => {
          const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
          return (
            <Link
              key={link.href}
              href={link.href}
              aria-current={active ? "page" : undefined}
              className={`min-h-11 rounded-md px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand ${
                active ? "text-brand" : "text-ink/70 hover:text-brand"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
