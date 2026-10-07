"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { StateMessage } from "@/components/StateMessage";
import { SearchInput } from "@/components/SearchInput";
import type { Subject, Term } from "@/lib/types";

export default function TermPage({ params }: { params: { termId: string } }) {
  const [term, setTerm] = useState<Term | null>(null);
  const [subjects, setSubjects] = useState<Subject[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [query, setQuery] = useState("");

  const load = useCallback(() => {
    setError(null);
    setTerm(null);
    setSubjects(null);
    Promise.all([
      api<Term>(`/terms/${params.termId}`),
      api<Subject[]>(`/subjects?term_id=${params.termId}`),
    ])
      .then(([loadedTerm, loadedSubjects]) => {
        setTerm(loadedTerm);
        setSubjects(loadedSubjects);
        document.title = `${loadedTerm.name} | NotesNest`;
      })
      .catch((reason: unknown) => {
        setError(reason instanceof ApiError ? reason : new ApiError("Couldn’t load this semester."));
      });
  }, [params.termId]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <section>
      <Link href="/" className="inline-flex min-h-11 items-center text-sm text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand">
        ← All semesters
      </Link>
      {error ? (
        <div className="mt-6">
          <StateMessage
            title={error.status === 404 ? "Semester not found." : "We couldn’t load this semester."}
            description={error.status === null ? "Check that the backend is running, then try again." : undefined}
            tone={error.status === 404 ? "default" : "error"}
            action={error.status === 404 ? undefined : { label: "Retry", onClick: load }}
          />
        </div>
      ) : !term || !subjects ? (
        <div className="mt-6"><StateMessage title="Loading subjects…" /></div>
      ) : (
        <>
          <p className="mt-8 text-sm font-semibold uppercase tracking-[0.18em] text-brand">{term.season} semester</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">{term.name}</h1>
          {subjects.length === 0 ? (
            <div className="mt-8">
              <StateMessage title="No subjects added for this semester yet." />
            </div>
          ) : (
            <>
              <div className="mt-8">
                <SearchInput
                  label="Search by subject code or name"
                  value={query}
                  onChange={setQuery}
                  placeholder="Search subjects"
                />
              </div>
              {(() => {
                const normalized = query.trim().toLowerCase();
                const filtered = subjects.filter(
                  (subject) =>
                    !normalized ||
                    subject.code.toLowerCase().includes(normalized) ||
                    subject.name.toLowerCase().includes(normalized),
                );
                return (
                  <>
                    <p className="mt-4 text-sm text-ink/60" aria-live="polite">
                      {filtered.length} {filtered.length === 1 ? "subject" : "subjects"}
                    </p>
                    {filtered.length === 0 ? (
                      <div className="mt-4">
                        <StateMessage title={`No subjects match “${query.trim()}”.`} />
                      </div>
                    ) : (
                      <ul className="mt-4 grid gap-4 sm:grid-cols-2">
                        {filtered.map((subject) => (
                          <li key={subject.id}>
                            <Link
                              href={`/subjects/${subject.id}`}
                              className="block min-h-28 rounded-xl border border-ink/10 bg-white p-5 transition hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
                            >
                              <p className="text-sm text-ink/60">{subject.code}</p>
                              <p className="mt-2 text-lg font-medium">{subject.name}</p>
                            </Link>
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                );
              })()}
            </>
          )}
        </>
      )}
    </section>
  );
}
