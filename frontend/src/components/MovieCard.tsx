import Image from "next/image";
import Link from "next/link";

import { posterUrl } from "@/lib/api";
import { MovieSearchResult } from "@/lib/types";

export default function MovieCard({ movie }: { movie: MovieSearchResult }) {
  const poster = posterUrl(movie.poster_path, "w500");
  const year = movie.release_date ? movie.release_date.slice(0, 4) : "TBA";

  return (
    <Link
      href={`/movies/${movie.tmdb_id}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-zinc-200 bg-white transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="relative aspect-[2/3] w-full bg-zinc-100 dark:bg-zinc-800">
        {poster ? (
          <Image
            src={poster}
            alt={movie.title}
            fill
            sizes="(max-width: 640px) 45vw, 185px"
            className="object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center px-2 text-center text-xs text-zinc-400">
            No poster
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <span className="line-clamp-2 text-sm font-medium text-zinc-900 group-hover:underline dark:text-zinc-50">
          {movie.title}
        </span>
        <span className="text-xs text-zinc-500 dark:text-zinc-400">{year}</span>
      </div>
    </Link>
  );
}
