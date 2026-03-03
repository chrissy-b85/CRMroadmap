import type { Statement } from "@/lib/types/statement";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.text().catch(() => res.statusText);
    throw new Error(error || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function getParticipantStatements(
  participantId: string,
): Promise<Statement[]> {
  return apiFetch<Statement[]>(
    `/api/v1/statements/participants/${participantId}`,
  );
}

export async function getStatement(
  participantId: string,
  year: number,
  month: number,
): Promise<Statement> {
  return apiFetch<Statement>(
    `/api/v1/statements/participants/${participantId}/${year}/${month}`,
  );
}

export async function generateStatement(
  participantId: string,
  year: number,
  month: number,
): Promise<Statement> {
  return apiFetch<Statement>(
    `/api/v1/statements/participants/${participantId}/${year}/${month}/generate`,
    { method: "POST" },
  );
}

export async function emailStatement(
  participantId: string,
  year: number,
  month: number,
): Promise<{ detail: string; status: string }> {
  return apiFetch(
    `/api/v1/statements/participants/${participantId}/${year}/${month}/email`,
    { method: "POST" },
  );
}

export async function getMyStatements(): Promise<Statement[]> {
  return apiFetch<Statement[]>("/api/v1/statements/my-statements");
}
