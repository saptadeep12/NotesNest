"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { ResourceRow } from "@/components/ResourceRow";
import { SearchInput } from "@/components/SearchInput";
import { StateMessage } from "@/components/StateMessage";
import { PaperRowSkeleton } from "@/components/ui/ListSkeletons";
import { Skeleton } from "@/components/ui/Skeleton";
import { ApiError, api } from "@/lib/api";
import type { Paper } from "@/lib/types";

function PapersContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const initialYear = searchParams.get("year") ?? "";
  const [query, setQuery] = useState(initialQuery);
  const [year, setYear] = useState(initialYear);
  const [years, setYears] = useState<number[]>([]);
  const [papers, setPapers] = useState<Paper[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const request = useRef<AbortController | null>(null);

  useEffect(() => {
    api<number[]>("/papers/years").then(setYears).catch(() => setYears([]));
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    const params = new URLSearchParams();
    if (trimmed) params.set("q", trimmed);
    if (year) params.set("year", year);
    const next = params.toString();
    router.replace(next ? `${pathname}?${next}` : pathname, { scroll: false });

    request.current?.abort();
    if (trimmed.length < 2) {
      setPapers(null);
      setLoading(false);
      setError(null);
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    setLoading(true);
    setError(null);
    const timer = window.setTimeout(() => {
      api<Paper[]>(
        `/papers?q=${encodeURIComponent(trimmed)}${year ? `&year=${encodeURIComponent(year)}` : ""}`,
        { signal: controller.signal },
      )
        .then((result) => {
          if (!controller.signal.aborted) setPapers(result);
        })
        .catch((reason: unknown) => {
          if (!controller.signal.aborted) {
            setError(reason instanceof ApiError ? reason : new ApiError("Couldn’t load papers."));
          }
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoading(false);
        });
    }, 300);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [pathname, query, retryCount, router, year]);

  const groups = useMemo(() => {
    const grouped = new Map<number, { code: string; name: string; papers: Paper[] }>();
    for (const paper of papers ?? []) {
      const group = grouped.get(paper.subject_id) ?? {
        code: paper.subject_code,
        name: paper.subject_name,
        papers: [],
      };
      group.papers.push(paper);
      grouped.set(paper.subject_id, group);
    }
    return [...grouped.entries()];
  }, [papers]);

  return (
    <section>
      <Link
        href="/"
        className="inline-flex min-h-11 items-center text-sm text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand"
      >
        ← Back to home
      </Link>
      <p className="mt-8 text-sm font-semibold uppercase tracking-[0.18em] text-brand">Paper finder</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-5xl">Search papers by subject</h1>
      <p className="mt-4 max-w-2xl text-base leading-7 text-ink/70">
        Know your subject code or name but not the semester? Find its CAT and FAT papers here.
      </p>
      <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-end">
        <SearchInput label="Subject code or name" value={query} onChange={setQuery} placeholder="e.g. MAT1101 or calculus" />
        <div className="max-w-md">
          <label htmlFor="paper-year" className="block text-sm font-medium">Year</label>
          <select id="paper-year" value={year} onChange={(event) => setYear(event.target.value)} className="mt-2 min-h-12 w-full rounded-lg border border-ink/20 bg-white px-3 py-3 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2">
            <option value="">Any year</option>
            {years.map((availableYear) => <option key={availableYear} value={availableYear}>{availableYear}</option>)}
          </select>
        </div>
      </div>
      <div id="paper-results" tabIndex={-1} aria-live="polite" aria-atomic="true">
      {query.trim().length < 2 ? (
        <p className="mt-8 text-sm text-ink/70">Type at least 2 characters of a subject code or name.</p>
      ) : loading ? (
        <div className="mt-8" aria-busy="true">
          <span className="sr-only" role="status">Loading...</span>
          <div className="space-y-8">
            <div>
              <SkeletonHeading />
              <ul className="mt-3 space-y-3" aria-busy="true">
                {Array.from({ length: 6 }, (_, index) => <PaperRowSkeleton key={index} />)}
              </ul>
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="mt-8">
          <StateMessage
            title="We couldn’t load the papers."
            description={error.status === null && process.env.NODE_ENV === "development" ? "Check that the backend is running on port 8000, then try again." : "Something went wrong while loading this page. Please try again in a moment."}
            tone="error"
            action={{ label: "Retry", onClick: () => setRetryCount((count) => count + 1) }}
          />
        </div>
      ) : groups.length === 0 ? (
        <div className="mt-8">
          <StateMessage title={`No papers found for “${query.trim()}”.`} description={year ? `No papers found for ${year}.` : undefined} />
        </div>
      ) : (
        <div className="mt-8 space-y-8">
          <p className="text-sm text-ink/75">{papers?.length ?? 0} {papers?.length === 1 ? "paper" : "papers"}</p>
          {groups.map(([subjectId, group]) => (
            <section key={subjectId} aria-labelledby={`subject-${subjectId}`}>
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 id={`subject-${subjectId}`} className="text-xl font-semibold">{group.code} <span className="font-normal text-ink/70">— {group.name}</span></h2>
                <Link href={`/subjects/${subjectId}?from=papers`} className="text-sm text-brand hover:underline">Open subject</Link>
              </div>
              <div className="mt-3"><ul className="space-y-3" aria-busy="false">{group.papers.map((paper) => <ResourceRow key={paper.id} resource={{ ...paper, subject_id: paper.subject_id, type: "pyq" }} />)}</ul></div>
            </section>
          ))}
        </div>
      )}
      </div>
    </section>
  );
}

export default function PapersPage() {
  return <Suspense fallback={<section className="mt-8"><span className="sr-only" role="status">Loading...</span><div className="space-y-8"><div><SkeletonHeading /><ul className="mt-3 space-y-3" aria-busy="true">{Array.from({ length: 6 }, (_, index) => <PaperRowSkeleton key={index} />)}</ul></div></div></section>}><PapersContent /></Suspense>;
}

function SkeletonHeading() {
  return (
    <div className="flex items-center justify-between gap-2">
      <Skeleton className="h-7 w-56" />
      <Skeleton className="h-5 w-24" />
    </div>
  );
}
