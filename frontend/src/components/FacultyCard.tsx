import type { Faculty } from "@/lib/types";

type FacultyCardProps = {
  faculty: Faculty;
  expanded: boolean;
  onToggle: () => void;
};

export function FacultyCard({ faculty, expanded, onToggle }: FacultyCardProps) {
  const hasDetails = Boolean(faculty.designation || faculty.email || faculty.cabin);
  const panelId = `faculty-details-${faculty.id}`;

  return (
    <li className="overflow-hidden rounded-xl border border-ink/10 bg-white">
      {hasDetails ? (
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={expanded}
          aria-controls={panelId}
          className="flex min-h-20 w-full items-center justify-between gap-4 px-5 py-4 text-left focus:outline-none focus:ring-2 focus:ring-inset focus:ring-brand"
        >
          <span className="min-w-0">
            <span className="block font-medium">{faculty.name}</span>
            {faculty.department && (
              <span className="mt-1 block text-sm text-ink/60">{faculty.department}</span>
            )}
          </span>
          <svg
            aria-hidden="true"
            viewBox="0 0 20 20"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className={`h-5 w-5 shrink-0 text-brand transition-transform ${expanded ? "rotate-180" : ""}`}
          >
            <path d="m5 7.5 5 5 5-5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      ) : (
        <div className="flex min-h-20 items-center px-5 py-4">
          <div>
            <p className="font-medium">{faculty.name}</p>
            {faculty.department && <p className="mt-1 text-sm text-ink/60">{faculty.department}</p>}
          </div>
        </div>
      )}
      {hasDetails && (
        <div
          id={panelId}
          className={`grid transition-[grid-template-rows] duration-200 ease-out ${
            expanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
          }`}
        >
          <div className="min-h-0 overflow-hidden">
            <div className="border-t border-ink/10 px-5 pb-5 pt-4 text-sm">
              {faculty.designation && <p>{faculty.designation}</p>}
              {faculty.email && (
                <p className="mt-2">
                  <a
                    href={`mailto:${faculty.email}`}
                    className="text-brand underline-offset-2 hover:underline focus:outline-none focus:ring-2 focus:ring-brand"
                  >
                    {faculty.email}
                  </a>
                </p>
              )}
              {faculty.cabin && <p className="mt-2 text-ink/70">Cabin: {faculty.cabin}</p>}
            </div>
          </div>
        </div>
      )}
    </li>
  );
}
