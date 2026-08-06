import React from "react"
import { Navigate, useLocation } from "react-router-dom"
import { useAuthStore } from "@/stores/auth-store"

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * Route guard that requires authentication.
 * Redirects to login page if user is not authenticated.
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const location = useLocation()

  if (!isAuthenticated) {
    // Redirect to login, preserving the intended destination
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

/**
 * Route guard that redirects authenticated users away from auth pages.
 * Example: redirect from /login to /app/dashboard if already logged in.
 */
export function PublicOnlyRoute({ children }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const location = useLocation()

  if (isAuthenticated) {
    // Redirect to intended destination or dashboard
    const from = (location.state as { from?: { pathname: string } })?.from?.pathname
    return <Navigate to={from || "/app/dashboard"} replace />
  }

  return <>{children}</>
}
