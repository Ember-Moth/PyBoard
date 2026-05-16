import { getAuthToken } from "@/lib/auth";
import { getApiBaseUrl } from "@/services/runtime-config.service";
import type { ApiResponse } from "@/types/api";

type RequestOptions = RequestInit & {
  auth?: boolean;
};

type ServiceOptions = Omit<RequestOptions, "body" | "method">;

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { auth = true, headers, ...init } = options;
  const token = getAuthToken();
  const requestHeaders = new Headers(headers);

  if (!requestHeaders.has("Content-Type") && init.body) {
    requestHeaders.set("Content-Type", "application/json");
  }
  if (auth && token) {
    requestHeaders.set("Authorization", token);
  }

  const response = await fetch(await apiUrl(endpoint), {
    ...init,
    headers: requestHeaders,
  });

  let payload: ApiResponse<T> | null = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    payload = (await response.json()) as ApiResponse<T>;
  }

  if (!response.ok) {
    throw new ApiError(payload?.msg || response.statusText || "请求失败", response.status);
  }
  if (payload && payload.code >= 400) {
    throw new ApiError(payload.msg || "请求失败", payload.code);
  }

  return (payload ? payload.data : null) as T;
}

export function get<T>(endpoint: string, options: ServiceOptions = {}): Promise<T> {
  return request<T>(endpoint, {
    ...options,
    method: "GET",
  });
}

export function post<T>(endpoint: string, body?: unknown, options: ServiceOptions = {}): Promise<T> {
  return request<T>(endpoint, {
    ...options,
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function patch<T>(endpoint: string, body?: unknown, options: ServiceOptions = {}): Promise<T> {
  return request<T>(endpoint, {
    ...options,
    method: "PATCH",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

async function apiUrl(endpoint: string): Promise<string> {
  if (/^https?:\/\//.test(endpoint)) {
    return endpoint;
  }
  return `${await getApiBaseUrl()}${endpoint}`;
}
