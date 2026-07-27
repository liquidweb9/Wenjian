import { QueryClientProvider } from "@tanstack/react-query"
import { RouterProvider } from "react-router-dom"
import { queryClient } from "./query-client"
import { router } from "./router"
import { AppErrorBoundary } from "./error-boundary"
import type { ReactNode } from "react"

export function AppProviders({ children }: { children?: ReactNode }) {
  return (
    <AppErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {children ?? <RouterProvider router={router} />}
      </QueryClientProvider>
    </AppErrorBoundary>
  )
}
