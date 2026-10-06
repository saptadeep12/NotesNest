import { fileUrl } from "@/lib/api";
import type { Resource } from "@/lib/types";

export function ResourceRow({ resource }: { resource: Resource }) {
  return (
    <li className="flex flex-col gap-4 rounded-xl border border-ink/10 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <p className="font-medium">{resource.title}</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {resource.exam && (
            <span className="rounded-full bg-brand/10 px-2.5 py-1 text-xs text-brand">
              {resource.exam}
            </span>
          )}
          {resource.year && (
            <span className="rounded-full bg-ink/5 px-2.5 py-1 text-xs text-ink/70">
              {resource.year}
            </span>
          )}
        </div>
      </div>
      <div className="flex shrink-0 gap-2">
        <a
          href={fileUrl(resource.id)}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-11 items-center justify-center rounded-lg border border-brand px-4 py-2 text-sm font-medium text-brand transition hover:bg-brand/5 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
        >
          View
        </a>
        <a
          href={fileUrl(resource.id, true)}
          download
          className="inline-flex min-h-11 items-center justify-center rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-dark focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
        >
          Download
        </a>
      </div>
    </li>
  );
}
