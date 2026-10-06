"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import { StateMessage } from "@/components/StateMessage";
import { ApiError, api } from "@/lib/api";
import type { Article } from "@/lib/types";

export default function AdviceArticlePage({ params }: { params: { slug: string } }) {
  const [article, setArticle] = useState<Article | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(() => {
    setError(null);
    setArticle(null);
    api<Article>(`/articles/${encodeURIComponent(params.slug)}`)
      .then((loaded) => {
        setArticle(loaded);
        document.title = `${loaded.title} | NotesNest`;
      })
      .catch((reason: unknown) => {
        setError(reason instanceof ApiError ? reason : new ApiError("Couldn’t load this article."));
      });
  }, [params.slug]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <article>
      <Link
        href="/advice"
        className="inline-flex min-h-11 items-center text-sm text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand"
      >
        ← All advice
      </Link>
      {error ? (
        <div className="mt-6">
          <StateMessage
            title={error.status === 404 ? "Article not found." : "We couldn’t load this article."}
            description={error.status === null ? "Check that the backend is running, then try again." : undefined}
            tone={error.status === 404 ? "default" : "error"}
            action={error.status === 404 ? undefined : { label: "Retry", onClick: load }}
          />
        </div>
      ) : !article ? (
        <p className="mt-6 animate-pulse text-ink/60">Loading article…</p>
      ) : (
        <>
          <header className="mt-8 border-b border-ink/10 pb-6">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand">{article.category}</p>
            <h1 className="mt-3 max-w-3xl text-3xl font-semibold tracking-tight sm:text-4xl">{article.title}</h1>
            <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-sm text-ink/60">
              {article.author && <span>By {article.author}</span>}
              <time dateTime={article.updated_at}>
                Updated {new Date(article.updated_at).toLocaleDateString()}
              </time>
            </div>
          </header>
          <div className="article-body mt-8">
            <ReactMarkdown
              components={{
                a: ({ href, children }) => {
                  const external = href?.startsWith("http://") || href?.startsWith("https://");
                  return (
                    <a
                      href={href}
                      target={external ? "_blank" : undefined}
                      rel={external ? "noopener noreferrer" : undefined}
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {article.body}
            </ReactMarkdown>
          </div>
        </>
      )}
    </article>
  );
}
