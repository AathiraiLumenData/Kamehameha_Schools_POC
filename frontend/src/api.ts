import type { AskResponse, GenieStatus, SpaceInfo } from "./types";

const API_BASE = "/api";

function getToken(): string {
  return localStorage.getItem("databricks_token") || "";
}

export function setToken(token: string) {
  localStorage.setItem("databricks_token", token);
}

export function getStoredToken(): string {
  return getToken();
}

export function clearToken() {
  localStorage.removeItem("databricks_token");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
      ...(init?.headers || {}),
    },
  });
  if (resp.status === 401) {
    throw new Error("AUTH_EXPIRED");
  }
  if (!resp.ok) {
    throw new Error(`API error: ${resp.status}`);
  }
  return resp.json();
}

export async function ask(
  question: string,
  conversationId?: string | null
): Promise<AskResponse> {
  return request<AskResponse>("/ask", {
    method: "POST",
    body: JSON.stringify({
      question,
      conversation_id: conversationId || undefined,
    }),
  });
}

export async function pollStatus(
  conversationId: string,
  messageId: string
): Promise<GenieStatus> {
  return request<GenieStatus>(`/status/${conversationId}/${messageId}`);
}

export async function fetchSpaceInfo(): Promise<SpaceInfo> {
  return request<SpaceInfo>("/space");
}
