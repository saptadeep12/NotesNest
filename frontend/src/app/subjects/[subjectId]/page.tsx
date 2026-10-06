"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { ResourceRow } from "@/components/ResourceRow";
import { StateMessage } from "@/components/StateMessage";
import { Tabs } from "@/components/Tabs";
import type { Resource, Subject } from "@/lib/types";

export default function SubjectPage({ params }: { params: { subjectId: string } }) {
  const [subject, setSubject] = useState<Subject | null>(null);
  const [resources, setResources] = useState<Resource[] | null>(null);
  const [selected, setSelected] = useState<"pyq" | "note">("pyq");
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(() => {
    setError(null);
    setSubject(null);
    setResources(null);
    Promise.all([
      api<Subject>(`/subjects/${params.subjectId}`),
      api<Resource[]>(`/resources?subject_id=${params.subjectId}`),
    ])
      .then(([loadedSubject, loadedResources]) => {
        setSubject(loadedSubject);
        setResources(loadedResources);
        document.title = `${loadedSubject.code} | NotesNest`;
      })
      .catch((reason: unknown) => {
        setError(reason instanceof ApiError ? reason : new ApiError("Couldn’t load this subject."));
      });
  }, [params.subjectId]);

  useEffect(() => {
    load();
  }, [load]);

  const pyqs = useMemo(() => resources?.filter((resource) => resource.type === "pyq") ?? [], [resources]);
  const notes = useMemo(() => resources?.filter((resource) => resource.type === "note") ?? [], [resources]);
  const currentResources = selected === "pyq" ? pyqs : notes;

  return (
    <section>
      <Link href="/" className="inline-flex min-h-11 items-center text-sm text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand">
        ← All semesters
      </Link>
      {error ? (
        <div className="mt-6">
          <StateMessage
            title={error.status === 404 ? "Subject not found." : "We couldn’t load this subject."}
            description={error.status === null ? "Check that the backend is running, then try again." : undefined}
            tone={error.status === 404 ? "default" : "error"}
            action={error.status === 404 ? undefined : { label: "Retry", onClick: load }}
          />
        </div>
      ) : !subject || !resources ? (
        <p className="mt-6 animate-pulse text-ink/60">Loading resources…</p>
      ) : (
        <>
          <div className="mt-8">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand">{subject.code}</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">{subject.name}</h1>
          </div>
          <div className="mt-10">
            <Tabs
              selected={selected}
              onChange={(id) => setSelected(id as "pyq" | "note")}
              tabs={[
                { id: "pyq", label: "PYQs", count: pyqs.length },
                { id: "note", label: "Notes", count: notes.length },
              ]}
            />
            <div id={`${selected}-panel`} role="tabpanel" aria-labelledby={`${selected}-tab`} className="pt-6">
              {currentResources.length === 0 ? (
                <StateMessage title={selected === "pyq" ? "No PYQs added for this subject yet." : "No notes added for this subject yet."} />
              ) : (
                <ul className="space-y-3">
                  {currentResources.map((resource) => (
                    <ResourceRow key={resource.id} resource={resource} />
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
