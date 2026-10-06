export type Term = {
  id: number;
  name: string;
  season: string;
  academic_year: string;
  is_freshers: boolean;
};

export type Subject = {
  id: number;
  code: string;
  name: string;
};

export type ResourceType = "pyq" | "note";

export type Resource = {
  id: number;
  subject_id: number;
  type: ResourceType;
  title: string;
  exam: string | null;
  year: number | null;
};

export type Faculty = {
  id: number;
  name: string;
  designation: string | null;
  department: string | null;
  email: string | null;
  cabin: string | null;
};

export type ArticleSummary = {
  id: number;
  slug: string;
  title: string;
  category: string;
  summary: string;
  author: string | null;
  order: number;
  updated_at: string;
};

export type Article = ArticleSummary & {
  body: string;
};
