import MovieSearchBar from "@/components/MovieSearchBar";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center bg-zinc-50 px-6 py-16 dark:bg-black">
      <main className="flex w-full max-w-4xl flex-col items-center gap-10">
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Movie Box Office Forecaster
          </h1>
          <p className="max-w-md text-sm text-zinc-600 dark:text-zinc-400">
            Look up any movie to see its box office performance, or search for an upcoming release to see a
            forecast.
          </p>
        </div>
        <MovieSearchBar />
      </main>
    </div>
  );
}
