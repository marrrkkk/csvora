"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/docs/overview", label: "Overview" },
  { href: "/docs/quickstart", label: "Quickstart" },
  { href: "/docs/authentication", label: "Authentication" },
  { href: "/docs/rate-limits", label: "Rate limits" },
  { href: "/docs/errors", label: "Errors" },
  { href: "/docs/import-lifecycle", label: "Import lifecycle" },
  { href: "/docs/analyze", label: "Analyze" },
  { href: "/docs/transform", label: "Transform" },
  { href: "/docs/results", label: "Results" },
  { href: "/docs/api-reference", label: "API reference" },
  { href: "/docs/changelog", label: "Changelog" },
];

export function DocsNav() {
  const pathname = usePathname();

  return (
    <nav className="flex flex-col gap-1">
      {nav.map((item) => {
        const active = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={[
              "rounded-md px-3 py-2 text-sm",
              active
                ? "bg-zinc-100 text-zinc-950 dark:bg-zinc-900 dark:text-white"
                : "text-zinc-700 hover:bg-zinc-50 hover:text-zinc-950 dark:text-zinc-300 dark:hover:bg-zinc-900 dark:hover:text-white",
            ].join(" ")}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

