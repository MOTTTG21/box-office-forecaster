import { HolidayHighlight } from "@/lib/types";

export default function HolidayBadge({ holiday }: { holiday: HolidayHighlight | null }) {
  if (!holiday) return null;

  return (
    <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm dark:border-amber-900 dark:bg-amber-950/40">
      <span className="font-medium text-amber-800 dark:text-amber-300">{holiday.label}</span>
      <span className="text-amber-700 dark:text-amber-400">&middot; {holiday.blurb}</span>
    </div>
  );
}
