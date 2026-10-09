"use client";

import Link from "next/link";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { ResourceRow } from "@/components/ResourceRow";
import { StateMessage } from "@/components/StateMessage";
import { Tabs } from "@/components/Tabs";
import { ApiError, api } from "@/lib/api";
import type { Resource, Subject } from "@/lib/types";

type GroupId = "cat" | "fat" | "note" | "other";

function byYearDescending(left: Resource, right: Resource): number {
  return (right.year ?? 0) - (left.year ?? 0);
}

function SubjectPageContent({ params }: { params: { subjectId: string } }) {
  const searchParams = useSearchParams();
  const termParam = searchParams.get("term");
  const termId =
    termParam && /^\d+$/.test(termParam) && Number(termParam) > 0
      ? termParam
      : null;
  const [subject, setSubject] = useState<Subject | null>(null);
  const [resources, setResources] = useState<Resource[] | null>(null);
  const [selected, setSelected] = useState<GroupId>("cat");
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

  const groups = useMemo(() => {
    const cat: Resource[] = [];
    const fatTheory: Resource[] = [];
    const fatLab: Resource[] = [];
    const notes: Resource[] = [];
    const other: Resource[] = [];

    for (const resource of resources ?? []) {
      if (resource.type === "note") {
        notes.push(resource);
      } else if (resource.exam?.startsWith("CAT")) {
        cat.push(resource);
      } else if (resource.exam === "FAT-Theory") {
        fatTheory.push(resource);
      } else if (resource.exam === "FAT-Lab") {
        fatLab.push(resource);
      } else {
        other.push(resource);
      }
    }

    cat.sort((left, right) => {
      const yearOrder = byYearDescending(left, right);
      if (yearOrder) return yearOrder;
      const rank = (exam: string | null) => (exam === "CAT-2" ? 0 : 1);
      return rank(left.exam) - rank(right.exam);
    });
    fatTheory.sort(byYearDescending);
    fatLab.sort(byYearDescending);
    return { cat, fatTheory, fatLab, notes, other };
  }, [resources]);

  const tabs = useMemo(
    () => [
      { id: "cat", label: "CAT", count: groups.cat.length },
      { id: "fat", label: "FAT", count: groups.fatTheory.length + groups.fatLab.length },
      ...(groups.notes.length ? [{ id: "note", label: "Notes", count: groups.notes.length }] : []),
      ...(groups.other.length ? [{ id: "other", label: "Other", count: groups.other.length }] : []),
    ],
    [groups],
  );

  useEffect(() => {
    if (!resources) return;
    const firstWithItems: GroupId =
      groups.cat.length > 0
        ? "cat"
        : groups.fatTheory.length + groups.fatLab.length > 0
          ? "fat"
          : groups.notes.length > 0
            ? "note"
            : groups.other.length > 0
              ? "other"
              : "cat";
    setSelected(firstWithItems);
  }, [groups, resources]);

  const renderRows = (items: Resource[], showExam = true) => (
    <ul className="space-y-3">
      {items.map((resource) => (
        <ResourceRow key={resource.id} resource={resource} showExam={showExam} />
      ))}
    </ul>
  );

  const renderContent = () => {
    if (selected === "cat") {
      return groups.cat.length
        ? renderRows(groups.cat)
        : <StateMessage title="No CAT papers added for this subject yet." />;
    }
    if (selected === "fat") {
      if (!groups.fatTheory.length && !groups.fatLab.length) {
        return <StateMessage title="No FAT papers added for this subject yet." />;
      }
      return (
        <div className="space-y-8">
          {groups.fatTheory.length > 0 && (
            <section aria-labelledby="fat-theory-heading">
              <h2 id="fat-theory-heading" className="mb-3 text-lg font-semibold">Theory</h2>
              {renderRows(groups.fatTheory, false)}
            </section>
          )}
          {groups.fatLab.length > 0 && (
            <section aria-labelledby="fat-lab-heading">
              <h2 id="fat-lab-heading" className="mb-3 text-lg font-semibold">Lab</h2>
              {renderRows(groups.fatLab, false)}
            </section>
          )}
        </div>
      );
    }
    const items = selected === "note" ? groups.notes : groups.other;
    return renderRows(items);
  };

  return (
    <section>
      <Link
        href={termId ? `/terms/${termId}` : "/"}
        className="inline-flex min-h-11 items-center text-sm text-brand hover:underline focus:outline-none focus:ring-2 focus:ring-brand"
      >
        {termId ? "← Back to subjects" : "← All semesters"}
      </Link>
      {error ? (
        <div className="mt-6">
          <StateMessage
            title={error.status === 404 ? "Subject not found." : "We couldn’t load this subject."}
            description={
              error.status === null
                ? process.env.NODE_ENV === "development"
                  ? "Check that the backend is running, then try again."
                  : "Something went wrong while loading this page. Please try again in a moment."
                : undefined
            }
            tone={error.status === 404 ? "default" : "error"}
            action={error.status === 404 ? undefined : { label: "Retry", onClick: load }}
          />
        </div>
      ) : !subject || !resources ? (
        <div className="mt-6"><StateMessage title="Loading resources…" /></div>
      ) : (
        <>
          <div className="mt-8">
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-brand">{subject.code}</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight">{subject.name}</h1>
          </div>
          <div className="mt-10">
            <Tabs
              selected={selected}
              onChange={(id) => setSelected(id as GroupId)}
              tabs={tabs}
            />
            <div id={`${selected}-panel`} role="tabpanel" aria-labelledby={`${selected}-tab`} className="pt-6">
              {renderContent()}
            </div>
          </div>
        </>
      )}
    </section>
  );
}

export default function SubjectPage({ params }: { params: { subjectId: string } }) {
  return (
    <Suspense fallback={<section className="mt-6"><StateMessage title="Loading resources…" /></section>}>
      <SubjectPageContent params={params} />
    </Suspense>
  );
}
