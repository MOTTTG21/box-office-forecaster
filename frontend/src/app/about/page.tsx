export default function AboutPage() {
  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 dark:bg-black">
      <div className="mx-auto flex w-full max-w-2xl flex-col gap-8 text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">About this site</h1>
          <p className="text-zinc-500 dark:text-zinc-400">
            A personal project that looks up real box office data and tries — honestly, imperfectly — to forecast
            it.
          </p>
        </div>

        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Where the data comes from</h2>
          <p>
            Movie metadata (cast, crew, budget, genres, posters) comes from{" "}
            <a href="https://www.themoviedb.org/" className="underline" target="_blank" rel="noreferrer">
              TMDB
            </a>
            . Actual box office numbers — weekly gross, lifetime totals — are scraped from Box Office Mojo the first
            time a movie is looked up on this site, then cached. Critic scores (Rotten Tomatoes, Metacritic, IMDb)
            come from{" "}
            <a href="https://www.omdbapi.com/" className="underline" target="_blank" rel="noreferrer">
              OMDb
            </a>
            .
          </p>
          <p>
            The database only contains movies someone has actually looked up here (plus a bit of automatic
            backfilling — when a movie needs a prediction, its director&apos;s past films get pulled in too, so
            there&apos;s real data to compare against). It grows as the site gets used, rather than starting
            complete.
          </p>
        </section>

        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">How the forecast works — and how well it works</h2>
          <p>
            The opening-weekend prediction on the This Week tab is a simple idea: look at a director&apos;s past
            films (or, failing that, films in the same genre), and scale their historical opening weekends by how
            this film&apos;s budget compares to theirs. If neither the film&apos;s budget nor a comparable film with
            a known budget is available, the site says so honestly instead of guessing — you&apos;ll see &ldquo;not
            enough data&rdquo; rather than a made-up number.
          </p>
          <p>
            I don&apos;t just claim this works — I tested it. Every prediction the model would have made for movies
            already in the database (leaving each movie out of its own comparison, so it&apos;s not cheating) gets
            checked against what actually happened. That backtest is scored only against movies that themselves
            opened wide (600+ theaters) — that&apos;s the population &ldquo;This Week&rdquo; actually predicts for.
            The database also holds smaller limited-release films that only got in via a director&apos;s
            auto-backfilled history, and no amount of comp-selection can fix a prediction for a film that was never
            going to open wide in the first place — including those would dilute the number with an unrelated,
            unsolvable case rather than make it more honest. Scored that way, the model&apos;s predictions are off
            by a median of about 67%. That&apos;s a heuristic — an educated guess built from historical averages —
            not a trained model, and this is an honest number, not a polished one.
          </p>
          <p>
            I also checked whether a film&apos;s critic score (Rotten Tomatoes) would help explain the model&apos;s
            misses, since that seemed like an obvious next signal. It doesn&apos;t, really — the correlation between
            critic score and prediction error came out to 0.14, essentially noise. So critic scores are shown on
            this site as useful information on their own, not folded into the forecast as an unproven fix.
          </p>
        </section>

        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">Inflation-adjusted figures</h2>
          <p>
            For any film that wasn&apos;t released this calendar year, budget and gross figures show a second,
            smaller line converting the dollar amount to today&apos;s dollars — so a 1975 movie&apos;s $9M budget
            reads alongside what that would cost to make now. The conversion uses the CPI-U (Consumer Price
            Index for All Urban Consumers), the standard general-purpose inflation measure, not a movie-ticket-
            specific price index — box office trackers sometimes use the latter, since ticket prices have
            historically outpaced general inflation, but that series isn&apos;t freely available. It&apos;s a
            directional &ldquo;what would this be worth today&rdquo; comparison, not a precise one.
          </p>
        </section>

        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">What &ldquo;Domestic Gross&rdquo; vs. &ldquo;Worldwide (estimated)&rdquo; means</h2>
          <p>
            Box Office Mojo publishes a real week-by-week breakdown for domestic (U.S./Canada) grosses, but only
            lifetime totals for international markets — there&apos;s no public weekly international feed to pull
            from. So the &ldquo;Worldwide&rdquo; view on a movie&apos;s chart is a labeled estimate: it takes the
            real domestic weekly shape and scales it by the film&apos;s actual domestic-to-worldwide ratio. It is
            not real international weekly data, and the site says so wherever it&apos;s shown.
          </p>
        </section>

        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-medium text-zinc-900 dark:text-zinc-50">The code</h2>
          <p>
            This is a portfolio project, built end-to-end (including the parts that didn&apos;t work at first) in
            the open.{" "}
            <a
              href="https://github.com/MOTTTG21/box-office-forecaster"
              className="underline"
              target="_blank"
              rel="noreferrer"
            >
              The full source, including the backtest script and the write-up of the real bugs it caught, is on
              GitHub.
            </a>
          </p>
        </section>
      </div>
    </div>
  );
}
