function rtColor(score: number): string {
  return score >= 60 ? "#0ca30c" : "#d03b3b";
}

function metacriticColor(score: number): string {
  if (score >= 61) return "#0ca30c";
  if (score >= 40) return "#fab219";
  return "#d03b3b";
}

export default function CriticScores({
  rottenTomatoesScore,
  metascore,
  imdbRating,
}: {
  rottenTomatoesScore: number | null;
  metascore: number | null;
  imdbRating: number | null;
}) {
  if (rottenTomatoesScore == null && metascore == null && imdbRating == null) return null;

  return (
    <div className="flex flex-wrap items-center gap-3 text-sm">
      {rottenTomatoesScore != null && (
        <span className="flex items-center gap-1 font-medium" style={{ color: rtColor(rottenTomatoesScore) }}>
          🍅 {rottenTomatoesScore}%
        </span>
      )}
      {metascore != null && (
        <span
          className="flex items-center gap-1 rounded px-1.5 py-0.5 text-xs font-semibold text-white"
          style={{ backgroundColor: metacriticColor(metascore) }}
        >
          {metascore}
        </span>
      )}
      {imdbRating != null && (
        <span className="flex items-center gap-1 font-medium text-zinc-700 dark:text-zinc-300">
          ⭐ {imdbRating.toFixed(1)}/10
        </span>
      )}
    </div>
  );
}
