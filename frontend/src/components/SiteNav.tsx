import Link from "next/link";

export default function SiteNav() {
  return (
    <nav className="flex items-center gap-6 border-b border-zinc-200 bg-white px-6 py-3 dark:border-zinc-800 dark:bg-black">
      <Link href="/" className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
        Box Office Forecaster
      </Link>
      <Link
        href="/"
        className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
      >
        Browse
      </Link>
      <Link
        href="/this-week"
        className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
      >
        This Week
      </Link>
      <Link
        href="/about"
        className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
      >
        About
      </Link>
    </nav>
  );
}
