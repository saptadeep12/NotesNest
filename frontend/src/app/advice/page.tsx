"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { StateMessage } from "@/components/StateMessage";
import { ApiError, api } from "@/lib/api";
import type { ArticleSummary } from "@/lib/types";

export default function AdvicePage() {
  const [articles, setArticles] = useState<ArticleSummary[] | null>(null);
  const [category, setCategory] = useState("All");
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(() => {
    setError(null);
    setArticles(null);
    api<ArticleSummary[]>("/articles")
      .then(setArticles)
      .catch((reason: unknown) => {
        setError(reason instanceof ApiError ? reason : new ApiError("Couldn’t load advice."));
      });
  }, []);

  useEffect(() => {
    load();
    document.title = "Advice | NotesNest";
  }, [load]);

  const categories = useMemo(
    () => ["All", ...Array.from(new Set((articles ?? []).map((article) => article.category)))],
    [articles],
  );
  const visibleArticles = useMemo(
    () =>
      category === "All"
        ? articles ?? []
        : (articles ?? []).filter((article) => article.category === category),
    [articles, category],
  );

  return (
    <section>
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand">Student notes</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Advice</h1>
      <p className="mt-3 max-w-xl text-ink/70">
        Practical ideas and experience, collected for students.
      </p>
      {error ? (
        <div className="mt-8">
          <StateMessage
            title="We couldn’t load the advice."
            description={
              error.status === null
                ? process.env.NODE_ENV === "development"
                  ? "Check that the backend is running on port 8000, then try again."
                  : "Something went wrong while loading this page. Please try again in a moment."
                : "Please try again in a moment."
            }
            tone="error"
            action={{ label: "Retry", onClick: load }}
          />
        </div>
      ) : !articles ? (
        <div className="mt-8"><StateMessage title="Loading articles…" /></div>
      ) : articles.length === 0 ? (
        <div className="mt-8">
          <StateMessage title="No articles yet." />
        </div>
      ) : (
        <>
          <div className="mt-8 flex flex-wrap gap-2" aria-label="Filter articles by category">
            {categories.map((item) => (
              <button
                key={item}
                type="button"
                aria-pressed={category === item}
                onClick={() => setCategory(item)}
                className={`min-h-11 rounded-full px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 ${
                  category === item
                    ? "bg-brand text-white"
                    : "border border-ink/15 bg-white text-ink/70 hover:border-brand/40 hover:text-brand"
                }`}
              >
                {item}
              </button>
            ))}
          </div>
          {visibleArticles.length === 0 ? (
            <div className="mt-6">
              <StateMessage title={`No articles in ${category} yet.`} />
            </div>
          ) : (
            <ul className="mt-6 grid gap-4 sm:grid-cols-2">
              {visibleArticles.map((article) => (
                <li key={article.id}>
                  <Link
                    href={`/advice/${article.slug}`}
                    className="block h-full rounded-xl border border-ink/10 bg-white p-5 transition hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.15em] text-brand">
                      {article.category}
                    </p>
                    <h2 className="mt-3 text-lg font-semibold">{article.title}</h2>
                    <p className="mt-2 text-sm leading-6 text-ink/70">{article.summary}</p>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
