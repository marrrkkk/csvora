import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "CSV Import Fixer",
    template: "%s · CSV Import Fixer",
  },
  description:
    "Production-ready API for fixing messy contact CSV imports: analyze structure, infer mappings, transform, validate, and export clean artifacts.",
  metadataBase: new URL("http://localhost:3000"),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "CSV Import Fixer",
    description:
      "Production-ready API for fixing messy contact CSV imports: analyze, map, transform, validate, and export clean artifacts.",
    url: "/",
    siteName: "CSV Import Fixer",
    type: "website",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-zinc-950 dark:bg-zinc-950 dark:text-zinc-50">
        <a
          href="#content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:text-zinc-950 focus:shadow dark:focus:bg-zinc-900 dark:focus:text-zinc-50"
        >
          Skip to content
        </a>

        <header className="border-b border-zinc-200/70 dark:border-zinc-800/70">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
            <Link href="/" className="font-semibold tracking-tight">
              CSV Import Fixer
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link
                href="/docs"
                className="text-zinc-700 hover:text-zinc-950 dark:text-zinc-300 dark:hover:text-white"
              >
                Docs
              </Link>
              <Link
                href="/docs/quickstart"
                className="rounded-md bg-zinc-950 px-3 py-2 text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-950 dark:hover:bg-zinc-200"
              >
                Get started
              </Link>
            </nav>
          </div>
        </header>

        <main id="content" className="flex-1">
          {children}
        </main>

        <footer className="border-t border-zinc-200/70 dark:border-zinc-800/70">
          <div className="mx-auto w-full max-w-6xl px-6 py-10 text-sm text-zinc-600 dark:text-zinc-400">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p>CSV Import Fixer — docs and landing.</p>
              <div className="flex gap-4">
                <Link
                  href="/docs"
                  className="hover:text-zinc-950 dark:hover:text-white"
                >
                  Docs
                </Link>
                <Link
                  href="/docs/api-reference"
                  className="hover:text-zinc-950 dark:hover:text-white"
                >
                  API reference
                </Link>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
