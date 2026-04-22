import Link from "next/link";

const pages = [
  { slug: "overview", title: "Overview", desc: "What the service does." },
  { slug: "quickstart", title: "Quickstart", desc: "Run locally and try the flow." },
  { slug: "authentication", title: "Authentication", desc: "API keys and headers." },
  { slug: "rate-limits", title: "Rate limits", desc: "Limiter behavior and headers." },
  { slug: "errors", title: "Errors", desc: "Error shapes and common cases." },
  { slug: "import-lifecycle", title: "Import lifecycle", desc: "Statuses and endpoints." },
  { slug: "analyze", title: "Analyze flow", desc: "Trigger analysis and read results." },
  { slug: "transform", title: "Transform flow", desc: "Approve mappings and transform." },
  { slug: "results", title: "Result retrieval", desc: "Artifacts and validation report." },
  { slug: "changelog", title: "Changelog", desc: "Placeholder for releases." },
  { slug: "api-reference", title: "API reference", desc: "OpenAPI-powered reference (Phase 5)." },
];

export default function DocsIndexPage() {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-12">
      <div className="max-w-2xl">
        <h1 className="text-3xl font-semibold tracking-tight">Docs</h1>
        <p className="mt-3 text-zinc-700 dark:text-zinc-300">
          Developer-first documentation for running, integrating, and operating the
          CSV Import Fixer API.
        </p>
      </div>

      <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {pages.map((p) => (
          <Link
            key={p.slug}
            href={`/docs/${p.slug}`}
            className="rounded-xl border border-zinc-200 p-5 shadow-sm hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
          >
            <p className="font-semibold text-zinc-950 dark:text-white">{p.title}</p>
            <p className="mt-2 text-sm leading-6 text-zinc-700 dark:text-zinc-300">
              {p.desc}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

