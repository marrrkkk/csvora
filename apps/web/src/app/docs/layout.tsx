import type { ReactNode } from "react";
import Link from "next/link";
import { DocsNav } from "./_components/DocsNav";

export default function DocsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-10">
      <div className="mb-8 flex items-baseline justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-950 dark:text-white">
            Documentation
          </h1>
          <p className="mt-2 text-sm text-zinc-700 dark:text-zinc-300">
            Developer-first docs and an OpenAPI-powered reference.
          </p>
        </div>
        <div className="flex gap-3 text-sm">
          <Link
            href="/"
            className="text-zinc-700 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-white"
          >
            Home
          </Link>
          <Link
            href="/docs/api-reference"
            className="text-zinc-700 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-white"
          >
            API reference
          </Link>
        </div>
      </div>

      <div className="grid gap-10 lg:grid-cols-[260px_1fr]">
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <div className="rounded-xl border border-zinc-200 p-3 dark:border-zinc-800">
            <DocsNav />
          </div>
        </aside>

        <section className="min-w-0">{children}</section>
      </div>
    </div>
  );
}

