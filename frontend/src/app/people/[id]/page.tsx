import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { getPerson, posterUrl } from "@/lib/api";
import FilmographyCard from "@/components/FilmographyCard";

export default async function PersonDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tmdbId = Number(id);

  let person;
  try {
    person = await getPerson(tmdbId);
  } catch {
    notFound();
  }

  const photo = posterUrl(person.profile_path, "original");

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-8">
        <Link href="/" className="text-sm text-zinc-500 hover:underline dark:text-zinc-400">
          &larr; Back to search
        </Link>

        <div className="flex flex-col gap-6 sm:flex-row">
          <div className="relative w-48 shrink-0">
            <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-zinc-200 dark:bg-zinc-800">
              {photo ? (
                <Image src={photo} alt={person.name} fill sizes="192px" className="object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-xs text-zinc-400">No photo</div>
              )}
            </div>
          </div>

          <div className="flex flex-1 flex-col gap-3">
            <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">{person.name}</h1>
            {person.known_for_department && (
              <span className="text-xs text-zinc-500 dark:text-zinc-400">{person.known_for_department}</span>
            )}
            {person.biography && (
              <p className="line-clamp-6 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                {person.biography}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Filmography</h2>
          {person.filmography.length > 0 ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              {person.filmography.map((item) => (
                <FilmographyCard key={`${item.tmdb_id}-${item.role}`} item={item} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">No filmography on record.</p>
          )}
        </div>
      </div>
    </div>
  );
}
