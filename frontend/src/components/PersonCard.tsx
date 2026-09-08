import Image from "next/image";
import Link from "next/link";

import { posterUrl } from "@/lib/api";
import { PersonSearchResult } from "@/lib/types";

export default function PersonCard({ person }: { person: PersonSearchResult }) {
  const photo = posterUrl(person.profile_path, "w342");

  return (
    <Link
      href={`/people/${person.tmdb_id}`}
      className="group flex flex-col overflow-hidden rounded-lg border border-zinc-200 bg-white transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
    >
      <div className="relative aspect-[2/3] w-full bg-zinc-100 dark:bg-zinc-800">
        {photo ? (
          <Image
            src={photo}
            alt={person.name}
            fill
            sizes="(max-width: 640px) 45vw, 185px"
            className="object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center px-2 text-center text-xs text-zinc-400">
            No photo
          </div>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <span className="line-clamp-2 text-sm font-medium text-zinc-900 group-hover:underline dark:text-zinc-50">
          {person.name}
        </span>
        {person.known_for_department && (
          <span className="text-xs text-zinc-500 dark:text-zinc-400">{person.known_for_department}</span>
        )}
      </div>
    </Link>
  );
}
