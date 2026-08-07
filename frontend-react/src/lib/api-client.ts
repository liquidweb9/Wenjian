import axios from "axios"

import { env } from "@/lib/env"

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly requestId?: string,
    public readonly fieldErrors?: Array<{ field: string; code: string; message: string }>,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export function getAuthToken(): string | null {
  const authStorage = localStorage.getItem("auth-storage")
  if (!authStorage) return null
  try {
    const { state } = JSON.parse(authStorage)
    return state?.token ?? null
  } catch {
    return null
  }
}

export const api = axios.create({
  baseURL: `${env.VITE_API_BASE_URL.replace(/\/$/, "")}/api/v1`,
  // Ordinary reads should fail fast. Long-running interview mutations override
  // this because one answer can legitimately execute several dependent LLM nodes.
  timeout: 120_000,
  headers: { "Content-Type": "application/json" },
})

// Request interceptor: inject request ID and auth token
api.interceptors.request.use((config) => {
  config.headers.set("X-Request-ID", crypto.randomUUID().slice(0, 12))

  // Inject auth token from localStorage if available
  const token = getAuthToken()
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`)
  }

  return config
})

// Response interceptor: normalize errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const data = error.response.data
      const err = data?.error ?? data
      throw new ApiError(
        error.response.status,
        err?.code ?? "UNKNOWN",
        err?.message ?? error.message,
        err?.request_id,
        err?.field_errors,
      )
    }
    throw new ApiError(0, "NETWORK_ERROR", error.message ?? "Network error")
  },
)
