import { notFound } from "next/navigation";
import Link from "next/link";
import fs from "node:fs";
import path from "node:path";

type DocMeta = {
  title: string;
  description?: string;
};

const DOCS_DIR = path.join(process.cwd(), "content", "docs");

function docPath(slug: string) {
  return path.join(DOCS_DIR, `${slug}.md`);
}

function readDoc(slug: string): { meta: DocMeta; content: string } | null {
  const p = docPath(slug);
  if (!fs.existsSync(p)) return null;

  const raw = fs.readFileSync(p, "utf-8");
  const lines = raw.split(/\r?\n/);
  const titleLine = lines.find((l) => l.trim().startsWith("# "));
  const title = titleLine ? titleLine.trim().slice(2).trim() : slug;

  // Very light metadata: first non-empty paragraph after title.
  const titleIndex = titleLine ? lines.indexOf(titleLine) : -1;
  const afterTitle = titleIndex >= 0 ? lines.slice(titleIndex + 1) : lines;
  const firstParagraph = afterTitle
    .join("\n")
    .split(/\n\s*\n/)
    .map((p2) => p2.trim())
    .find((p2) => p2.length > 0 && !p2.startsWith("#"));

  return { meta: { title, description: firstParagraph }, content: raw };
}

function renderMarkdown(md: string): string {
  // Minimal, intentionally boring markdown renderer:
  // - headings (#, ##, ###)
  // - fenced code blocks ```...```
  // - paragraphs
  // - unordered lists (- ...)
  //
  // This keeps Phase 4 simple; MDX + richer rendering can be added later
  // without changing content paths.
  const escaped = (s: string) =>
    s
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");

  const lines = md.split(/\r?\n/);
  const out: string[] = [];
  let inCode = false;
  let codeLang = "";
  let codeBuf: string[] = [];
  let listBuf: string[] = [];

  const flushList = () => {
    if (listBuf.length === 0) return;
    out.push(
      `<ul class="my-4 list-disc pl-6 text-zinc-700 dark:text-zinc-300">` +
        listBuf.map((li) => `<li class="my-1">${li}</li>`).join("") +
        `</ul>`
    );
    listBuf = [];
  };

  const flushCode = () => {
    if (!inCode) return;
    const code = escaped(codeBuf.join("\n"));
    const label = codeLang ? `<div class="text-xs text-zinc-500">${escaped(codeLang)}</div>` : "";
    out.push(
      `<div class="my-5 overflow-hidden rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900">` +
        `<div class="px-4 py-2 border-b border-zinc-200/70 dark:border-zinc-800/70">${label}</div>` +
        `<pre class="overflow-x-auto p-4 text-sm leading-6"><code>${code}</code></pre>` +
        `</div>`
    );
    inCode = false;
    codeLang = "";
    codeBuf = [];
  };

  const flushParagraph = (p: string) => {
    const t = p.trim();
    if (!t) return;
    out.push(`<p class="my-4 leading-7 text-zinc-700 dark:text-zinc-300">${escaped(t)}</p>`);
  };

  let paraBuf: string[] = [];
  const flushParaBuf = () => {
    const p = paraBuf.join(" ").trim();
    paraBuf = [];
    flushParagraph(p);
  };

  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      flushList();
      flushParaBuf();
      if (!inCode) {
        inCode = true;
        codeLang = line.trim().slice(3).trim();
      } else {
        flushCode();
      }
      continue;
    }

    if (inCode) {
      codeBuf.push(line);
      continue;
    }

    const h3 = line.match(/^###\s+(.*)$/);
    if (h3) {
      flushList();
      flushParaBuf();
      out.push(`<h3 class="mt-8 text-lg font-semibold tracking-tight text-zinc-950 dark:text-white">${escaped(h3[1])}</h3>`);
      continue;
    }
    const h2 = line.match(/^##\s+(.*)$/);
    if (h2) {
      flushList();
      flushParaBuf();
      out.push(`<h2 class="mt-10 text-2xl font-semibold tracking-tight text-zinc-950 dark:text-white">${escaped(h2[1])}</h2>`);
      continue;
    }
    const h1 = line.match(/^#\s+(.*)$/);
    if (h1) {
      flushList();
      flushParaBuf();
      out.push(`<h1 class="text-3xl font-semibold tracking-tight text-zinc-950 dark:text-white">${escaped(h1[1])}</h1>`);
      continue;
    }

    const li = line.match(/^\-\s+(.*)$/);
    if (li) {
      flushParaBuf();
      listBuf.push(escaped(li[1]));
      continue;
    }

    if (line.trim() === "") {
      flushList();
      flushParaBuf();
      continue;
    }

    paraBuf.push(line.trim());
  }

  flushList();
  flushParaBuf();
  flushCode();
  return out.join("\n");
}

export default function DocPage({ params }: { params: { slug: string } }) {
  const { slug } = params;
  const doc = readDoc(slug);
  if (!doc) return notFound();

  const html = renderMarkdown(doc.content);

  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-12">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-zinc-600 dark:text-zinc-400">
            <Link href="/docs" className="hover:underline">
              Docs
            </Link>{" "}
            / <span className="text-zinc-500">{slug}</span>
          </p>
        </div>
        <Link
          href="/docs/api-reference"
          className="text-sm text-zinc-700 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-white"
        >
          API reference
        </Link>
      </div>

      <article className="mt-6 max-w-3xl">
        <div dangerouslySetInnerHTML={{ __html: html }} />
      </article>
    </div>
  );
}

export function generateStaticParams() {
  if (!fs.existsSync(DOCS_DIR)) return [];
  return fs
    .readdirSync(DOCS_DIR)
    .filter((f) => f.endsWith(".md"))
    .map((f) => ({ slug: f.replace(/\.md$/, "") }));
}

