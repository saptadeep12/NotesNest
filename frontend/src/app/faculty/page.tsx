"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { FacultyCard } from "@/components/FacultyCard";
import { StateMessage } from "@/components/StateMessage";
import { ApiError, api } from "@/lib/api";
import type { Faculty } from "@/lib/types";

export default function FacultyPage() {
  const [faculty, setFaculty] = useState<Faculty[] | null>(null);
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(() => {
    setError(null);
    setFaculty(null);
    api<Faculty[]>("/faculty")
      .then((people) => {
        setFaculty(people);
        document.title = "Faculty | NotesNest";
      })
      .catch((reason: unknown) => {
        setError(reason instanceof ApiError ? reason : new ApiError("Couldn’t load faculty."));
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filteredFaculty = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!faculty || !normalized) return faculty ?? [];
    return faculty.filter(
      (person) =>
        person.name.toLowerCase().includes(normalized) ||
        (person.department?.toLowerCase().includes(normalized) ?? false),
    );
  }, [faculty, query]);

  const toggle = (id: number) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand">People</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Faculty</h1>
      <p className="mt-3 max-w-xl text-ink/70">Find contact details for the people who teach your course.</p>

      {error ? (
        <div className="mt-8">
          <StateMessage
            title="We couldn’t load the faculty directory."
            description={
              error.status === null
                ? "Check that the backend is running on port 8000, then try again."
                : "Please try again in a moment."
            }
            tone="error"
            action={{ label: "Retry", onClick: load }}
          />
        </div>
      ) : !faculty ? (
        <div className="mt-8 h-12 animate-pulse rounded-lg bg-ink/10" aria-label="Loading faculty" />
      ) : faculty.length === 0 ? (
        <div className="mt-8">
          <StateMessage title="No faculty added yet." />
        </div>
      ) : (
        <>
          <label htmlFor="faculty-search" className="mt-8 block text-sm font-medium">
            Search by name or department
          </label>
          <input
            id="faculty-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search faculty"
            className="mt-2 min-h-12 w-full rounded-lg border border-ink/20 bg-white px-3 py-3 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 sm:max-w-md"
          />
          <p className="mt-4 text-sm text-ink/60" aria-live="polite">
            {filteredFaculty.length} faculty
          </p>
          {filteredFaculty.length === 0 ? (
            <div className="mt-4">
              <StateMessage title={`No results for “${query}”.`} />
            </div>
          ) : (
            <ul className="mt-4 space-y-3">
              {filteredFaculty.map((person) => (
                <FacultyCard
                  key={person.id}
                  faculty={person}
                  expanded={expanded.has(person.id)}
                  onToggle={() => toggle(person.id)}
                />
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
