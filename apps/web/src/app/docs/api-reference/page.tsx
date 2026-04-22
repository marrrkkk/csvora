"use client";

import dynamic from "next/dynamic";
import Link from "next/link";

const RedocStandalone = dynamic(
  async () => {
    const mod = await import("redoc");
    return mod.RedocStandalone;
  },
  { ssr: false }
);

export default function ApiReferencePage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-12">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            <Link href="/docs" className="hover:underline">
              Docs
            </Link>{" "}
            / <span className="text-zinc-500">api-reference</span>
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-950 dark:text-white">
            API reference
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-700 dark:text-zinc-300">
            Rendered from the backend OpenAPI spec. Source of truth remains in{" "}
            <span className="font-medium">apps/api</span>.
          </p>
        </div>
        <a
          href="/openapi.json"
          className="text-sm text-zinc-700 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-white"
        >
          Download openapi.json
        </a>
      </div>

      <div className="mt-8 rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="p-4 text-sm text-zinc-600 dark:text-zinc-400">
          If this page is blank, run the OpenAPI sync:
          <span className="ml-2 font-mono">py -3 scripts/openapi_sync.py</span>
        </div>
        <div className="border-t border-zinc-200/70 dark:border-zinc-800/70">
          <RedocStandalone specUrl="/openapi.json" />
        </div>
      </div>
    </div>
  );
}

