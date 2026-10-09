"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, api } from "@/lib/api";
import type { Term } from "@/lib/types";
import { StateMessage } from "@/components/StateMessage";

export default function Home() {
  const router = useRouter();
  const [terms, setTerms] = useState<Term[] | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const loadTerms = () => {
    setError(null);
    setTerms(null);
    api<Term[]>("/terms").then(setTerms).catch((reason: unknown) => {
      setError(reason instanceof ApiError ? reason : new ApiError("Couldn’t load semesters."));
    });
  };

  useEffect(() => {
    loadTerms();
  }, []);

  return (
    <section className="py-4 sm:py-10">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand">Your study shelf</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-5xl">Find your subjects</h1>
      <p className="mt-4 max-w-xl text-base leading-7 text-ink/70">
        Previous-year papers and notes, organised by semester and subject.
      </p>

      <div className="mt-10 max-w-md">
        <label htmlFor="term" className="block text-sm font-medium">
          Choose a semester
        </label>
        {!terms && !error && <div className="mt-2"><StateMessage title="Loading semesters…" /></div>}
        {terms && (
          <select
            id="term"
            defaultValue=""
            onChange={(event) => event.target.value && router.push(`/terms/${event.target.value}`)}
            className="mt-2 min-h-12 w-full rounded-lg border border-ink/20 bg-white px-3 py-3 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
          >
            <option value="" disabled>
              -- Choose Semester --
            </option>
            {terms.map((term) => (
              <option key={term.id} value={term.id}>
                {term.name}
              </option>
            ))}
          </select>
        )}
        {error && (
          <div className="mt-3">
            <StateMessage
              title="We couldn’t load the semesters."
              description={
                error.status === null
                  ? process.env.NODE_ENV === "development"
                    ? "Check that the backend is running on port 8000, then try again."
                    : "Something went wrong while loading this page. Please try again in a moment."
                  : "Please try again in a moment."
              }
              tone="error"
              action={{ label: "Retry", onClick: loadTerms }}
            />
          </div>
        )}
      </div>
    </section>
  );
}
