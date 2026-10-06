const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number | null;

  constructor(message: string, status: number | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1${path}`, init);
  } catch {
    throw new ApiError("The backend is unreachable.");
  }
  if (!res.ok) {
    throw new ApiError(`API request failed: ${path}`, res.status);
  }
  return res.json() as Promise<T>;
}

export function fileUrl(id: number, download = false): string {
  const suffix = download ? "?download=1" : "";
  return `${API_URL}/api/v1/resources/${id}/file${suffix}`;
}
