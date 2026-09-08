"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef } from "react";

import { posterUrl } from "@/lib/api";
import { MovieSearchResult } from "@/lib/types";

const AUTO_SCROLL_INTERVAL_MS = 40;
const AUTO_SCROLL_PIXELS_PER_TICK = 1;

export default function MovieRow({
  title,
  movies,
  autoScroll = false,
}: {
  title: string;
  movies: MovieSearchResult[];
  autoScroll?: boolean;
}) {
  const scrollerRef = useRef<HTMLDivElement>(null);
  const isPausedRef = useRef(false);

  function scrollByAmount(direction: "left" | "right") {
    const el = scrollerRef.current;
    if (!el) return;
    const amount = el.clientWidth * 0.8 * (direction === "left" ? -1 : 1);
    el.scrollBy({ left: amount, behavior: "smooth" });
  }

  useEffect(() => {
    if (!autoScroll) return;
    const el = scrollerRef.current;
    if (!el) return;

    // The row's content is rendered twice back-to-back (see displayMovies below), so there's
    // always more to scroll into. Once scrolled past one full set's width, jump back by that
    // width with no animation - the duplicated content lines up exactly at that point, so the
    // wrap is invisible and the loop feels endless instead of visibly rewinding.
    const setWidth = el.scrollWidth / 2;

    const interval = setInterval(() => {
      if (isPausedRef.current) return;
      el.scrollLeft += AUTO_SCROLL_PIXELS_PER_TICK;
      if (el.scrollLeft >= setWidth) {
        el.scrollLeft -= setWidth;
      }
    }, AUTO_SCROLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [autoScroll, movies]);

  if (movies.length === 0) return null;

  const displayMovies = autoScroll ? [...movies, ...movies] : movies;

  return (
    <section className="flex flex-col gap-3">
      <h2 className="px-6 text-lg font-semibold text-zinc-900 dark:text-zinc-50 sm:px-0">{title}</h2>

      <div
        className="group/row relative"
        onMouseEnter={() => {
          isPausedRef.current = true;
        }}
        onMouseLeave={() => {
          isPausedRef.current = false;
        }}
      >
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
          className="flex gap-3 overflow-x-auto px-6 pb-2 [-ms-overflow-style:none] [scrollbar-width:none] sm:px-0 [&::-webkit-scrollbar]:hidden"
        >
          {displayMovies.map((movie, index) => {
            const poster = posterUrl(movie.poster_path, "w500");
            return (
              <Link
                key={`${movie.tmdb_id}-${index}`}
                href={`/movies/${movie.tmdb_id}`}
                className="group/card relative w-[140px] shrink-0 overflow-hidden rounded-md bg-zinc-200 transition-transform duration-200 ease-out hover:z-10 hover:scale-110 dark:bg-zinc-800 sm:w-[160px]"
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
