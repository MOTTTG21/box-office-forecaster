export default function PageSkeleton() {
  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-5xl animate-pulse flex-col gap-6">
        <div className="flex flex-col gap-2">
          <div className="h-8 w-72 rounded bg-zinc-200 dark:bg-zinc-800" />
          <div className="h-4 w-96 rounded bg-zinc-200 dark:bg-zinc-800" />
        </div>
        <div className="h-64 w-full rounded-lg bg-zinc-200 dark:bg-zinc-800" />
        <div className="flex flex-col gap-2">
          <div className="h-4 w-full rounded bg-zinc-200 dark:bg-zinc-800" />
          <div className="h-4 w-full rounded bg-zinc-200 dark:bg-zinc-800" />
          <div className="h-4 w-3/4 rounded bg-zinc-200 dark:bg-zinc-800" />
        </div>
      </div>
    </div>
  );
}
