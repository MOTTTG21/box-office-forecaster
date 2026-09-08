"use client";

import Image from "next/image";
import Link from "next/link";
import { useRef } from "react";

import { posterUrl } from "@/lib/api";
import { MovieSearchResult } from "@/lib/types";

export default function MovieRow({ title, movies }: { title: string; movies: MovieSearchResult[] }) {
  const scrollerRef = useRef<HTMLDivElement>(null);

  function scrollByAmount(direction: "left" | "right") {
    const el = scrollerRef.current;
    if (!el) return;
    const amount = el.clientWidth * 0.8 * (direction === "left" ? -1 : 1);
    el.scrollBy({ left: amount, behavior: "smooth" });
  }

  if (movies.length === 0) return null;

  return (
    <section className="flex flex-col gap-3">
      <h2 className="px-6 text-lg font-semibold text-zinc-900 dark:text-zinc-50 sm:px-0">{title}</h2>

      <div className="group/row relative">
        <button
          type="button"
          onClick={() => scrollByAmount("left")}
          aria-label={`Scroll ${title} left`}
          className="absolute left-0 top-0 z-10 hidden h-full w-10 items-center justify-center bg-gradient-to-r from-zinc-50 to-transparent opacity-0 transition-opacity group-hover/row:opacity-100 hover:!opacity-100 dark:from-black sm:flex"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-black/70 text-white">
            &#8249;
          </span>
        </button>

        <div
          ref={scrollerRef}
          className="flex gap-3 overflow-x-auto scroll-smooth px-6 pb-2 [-ms-overflow-style:none] [scrollbar-width:none] sm:px-0 [&::-webkit-scrollbar]:hidden"
          style={{ scrollSnapType: "x mandatory" }}
        >
          {movies.map((movie) => {
            const poster = posterUrl(movie.poster_path, "w500");
            return (
              <Link
                key={movie.tmdb_id}
                href={`/movies/${movie.tmdb_id}`}
                className="group/card relative w-[140px] shrink-0 overflow-hidden rounded-md bg-zinc-200 transition-transform duration-200 ease-out hover:z-10 hover:scale-110 dark:bg-zinc-800 sm:w-[160px]"
                style={{ scrollSnapAlign: "start" }}
              >
                <div className="relative aspect-[2/3] w-full">
                  {poster ? (
                    <Image
                      src={poster}
                      alt={movie.title}
                      fill
                      sizes="160px"
                      className="object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center px-2 text-center text-xs text-zinc-400">
                      No poster
                    </div>
                  )}
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-2 opacity-0 transition-opacity group-hover/card:opacity-100">
                    <span className="line-clamp-2 text-xs font-medium text-white">{movie.title}</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        <button
          type="button"
          onClick={() => scrollByAmount("right")}
          aria-label={`Scroll ${title} right`}
          className="absolute right-0 top-0 z-10 hidden h-full w-10 items-center justify-center bg-gradient-to-l from-zinc-50 to-transparent opacity-0 transition-opacity group-hover/row:opacity-100 hover:!opacity-100 dark:from-black sm:flex"
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-black/70 text-white">
            &#8250;
          </span>
        </button>
      </div>
    </section>
  );
}
