import Link from "next/link";

export default function Home() {
  return (
    <div className="bg-white dark:bg-zinc-950">
      <section className="mx-auto w-full max-w-6xl px-6 py-16 sm:py-24">
        <div className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <div className="flex flex-col gap-6">
            <p className="text-sm font-medium text-zinc-600 dark:text-zinc-400">
              Fix messy contact CSV imports—reliably.
            </p>
            <h1 className="text-4xl font-semibold tracking-tight text-zinc-950 dark:text-white sm:text-5xl">
              CSV Import Fixer API
            </h1>
            <p className="text-lg leading-8 text-zinc-700 dark:text-zinc-300">
              Upload a messy CSV, analyze structure, approve mappings, transform
              and validate rows, then download cleaned CSV/JSON artifacts with a
              detailed validation report.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row">
              <Link
                href="/docs/quickstart"
                className="inline-flex items-center justify-center rounded-md bg-zinc-950 px-5 py-3 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-950 dark:hover:bg-zinc-200"
              >
                Get started
              </Link>
              <Link
                href="/docs"
                className="inline-flex items-center justify-center rounded-md border border-zinc-200 px-5 py-3 text-sm font-medium text-zinc-950 hover:bg-zinc-50 dark:border-zinc-800 dark:text-white dark:hover:bg-zinc-900"
              >
                Read docs
              </Link>
              <Link
                href="/docs/api-reference"
                className="inline-flex items-center justify-center rounded-md border border-zinc-200 px-5 py-3 text-sm font-medium text-zinc-950 hover:bg-zinc-50 dark:border-zinc-800 dark:text-white dark:hover:bg-zinc-900"
              >
                API reference
              </Link>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-500">
              API key + rate limits supported. OpenAPI-powered reference arrives
              in Phase 5.
            </p>
          </div>

          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
            <div className="flex flex-col gap-4 text-sm">
              <p className="font-semibold text-zinc-950 dark:text-white">
                Developer-first flow
              </p>
              <ol className="grid gap-3 text-zinc-700 dark:text-zinc-300">
                <li>
                  <span className="font-medium text-zinc-950 dark:text-white">
                    1.
                  </span>{" "}
                  Create import
                </li>
                <li>
                  <span className="font-medium text-zinc-950 dark:text-white">
                    2.
                  </span>{" "}
                  Upload CSV
                </li>
                <li>
                  <span className="font-medium text-zinc-950 dark:text-white">
                    3.
                  </span>{" "}
                  Analyze (async)
                </li>
                <li>
                  <span className="font-medium text-zinc-950 dark:text-white">
                    4.
                  </span>{" "}
                  Approve mappings
                </li>
                <li>
                  <span className="font-medium text-zinc-950 dark:text-white">
                    5.
                  </span>{" "}
                  Transform + validate (async)
                </li>
                <li>
                  <span className="font-medium text-zinc-950 dark:text-white">
                    6.
                  </span>{" "}
                  Fetch results + artifacts
                </li>
              </ol>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-zinc-200/70 dark:border-zinc-800/70">
        <div className="mx-auto w-full max-w-6xl px-6 py-14">
          <h2 className="text-2xl font-semibold tracking-tight text-zinc-950 dark:text-white">
            Features
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: "Schema inference",
                desc: "Detect delimiter/encoding/header and infer mappings to canonical contacts fields.",
              },
              {
                title: "Normalization",
                desc: "Trim, normalize email/phone/country/tags, and produce consistent output artifacts.",
              },
              {
                title: "Validation report",
                desc: "Row-level issues with errors/warnings; empty rows skipped with explicit signals.",
              },
              {
                title: "Async pipeline",
                desc: "Analyze + transform run in background via Celery/Redis; status is queryable.",
              },
              {
                title: "Operator-ready",
                desc: "Health/readiness probes, metrics endpoint, and runbooks for triage and operations.",
              },
              {
                title: "OpenAPI-driven",
                desc: "API reference will be rendered from the backend OpenAPI spec (no duplication).",
              },
            ].map((f) => (
              <div
                key={f.title}
                className="rounded-xl border border-zinc-200 p-5 shadow-sm dark:border-zinc-800"
              >
                <p className="font-semibold text-zinc-950 dark:text-white">
                  {f.title}
                </p>
                <p className="mt-2 text-sm leading-6 text-zinc-700 dark:text-zinc-300">
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-zinc-200/70 dark:border-zinc-800/70">
        <div className="mx-auto w-full max-w-6xl px-6 py-14">
          <h2 className="text-2xl font-semibold tracking-tight text-zinc-950 dark:text-white">
            How it works
          </h2>
          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            {[
              {
                title: "Analyze",
                desc: "Detect structure and propose column mappings with confidence scores.",
              },
              {
                title: "Transform",
                desc: "Apply approved mappings, normalize values, validate rows, and generate artifacts.",
              },
              {
                title: "Retrieve",
                desc: "Fetch status/results and download cleaned CSV/JSON + validation report references.",
              },
            ].map((s) => (
              <div
                key={s.title}
                className="rounded-xl bg-zinc-50 p-6 dark:bg-zinc-900"
              >
                <p className="font-semibold text-zinc-950 dark:text-white">
                  {s.title}
                </p>
                <p className="mt-2 text-sm leading-6 text-zinc-700 dark:text-zinc-300">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-zinc-200/70 dark:border-zinc-800/70">
        <div className="mx-auto w-full max-w-6xl px-6 py-14">
          <div className="grid gap-8 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight text-zinc-950 dark:text-white">
                Pricing
              </h2>
              <p className="mt-2 text-sm leading-6 text-zinc-700 dark:text-zinc-300">
                Placeholder. Pricing and API key self-serve flow can be added
                later without changing the core backend scope.
              </p>
            </div>
            <div className="rounded-xl border border-zinc-200 p-6 dark:border-zinc-800">
              <p className="font-semibold text-zinc-950 dark:text-white">
                Developer-first CTA
              </p>
              <p className="mt-2 text-sm leading-6 text-zinc-700 dark:text-zinc-300">
                Start with local Docker, then deploy. Docs include auth, rate
                limits, errors, and full import flow.
              </p>
              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/docs/quickstart"
                  className="inline-flex items-center justify-center rounded-md bg-zinc-950 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-950 dark:hover:bg-zinc-200"
                >
                  Quickstart
                </Link>
                <Link
                  href="/docs/authentication"
                  className="inline-flex items-center justify-center rounded-md border border-zinc-200 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-zinc-50 dark:border-zinc-800 dark:text-white dark:hover:bg-zinc-900"
                >
                  Auth
                </Link>
                <span className="inline-flex items-center justify-center rounded-md border border-dashed border-zinc-300 px-4 py-2 text-sm text-zinc-600 dark:border-zinc-700 dark:text-zinc-300">
                  Get API key (placeholder)
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
