import { lazy, Suspense } from "react"
import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout } from "@/components/layout/AppLayout"
import { InterviewLayout } from "@/components/layout/InterviewLayout"

const DashboardPage = lazy(() => import("@/features/dashboard/pages/dashboard-page"))
const ResumeListPage = lazy(() => import("@/features/resumes/pages/resume-list-page"))
const ResumeUploadPage = lazy(() => import("@/features/resumes/pages/resume-upload-page"))
const ResumeReviewPage = lazy(() => import("@/features/resumes/pages/resume-review-page"))
const ResumeProfilePage = lazy(() => import("@/features/resumes/pages/resume-profile-page"))
const ResumeClaimsPage = lazy(() => import("@/features/resumes/pages/resume-claims-page"))
const InterviewListPage = lazy(() => import("@/features/interviews/pages/interview-list-page"))
const InterviewCreatePage = lazy(() => import("@/features/interviews/pages/interview-create-page"))
const InterviewRoomPage = lazy(() => import("@/features/interviews/pages/interview-room-page"))
const InterviewReportPage = lazy(() => import("@/features/reports/pages/interview-report-page"))
const AnalyticsPage = lazy(() => import("@/features/analytics/pages/analytics-page"))
const SettingsPage = lazy(() => import("@/features/settings/pages/settings-page"))
const LoginPage = lazy(() => import("@/features/auth/pages/login-page"))
const NotFoundPage = lazy(() => import("@/components/common/not-found-page"))

function Loading() {
  return (
    <div style={{ padding: "2.25rem", textAlign: "center", color: "var(--wj-text-secondary)" }}>
      问鉴正在准备页面内容…
    </div>
  )
}

function LazyRoute({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<Loading />}>{children}</Suspense>
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: (
      <LazyRoute>
        <LoginPage />
      </LazyRoute>
    ),
  },
  {
    path: "/app",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="dashboard" replace /> },
      { path: "dashboard", element: <LazyRoute><DashboardPage /></LazyRoute> },
      { path: "resumes", element: <LazyRoute><ResumeListPage /></LazyRoute> },
      { path: "resumes/new", element: <LazyRoute><ResumeUploadPage /></LazyRoute> },
      { path: "resumes/:resumeId/review", element: <LazyRoute><ResumeReviewPage /></LazyRoute> },
      { path: "resumes/:resumeId/profile", element: <LazyRoute><ResumeProfilePage /></LazyRoute> },
      { path: "resumes/:resumeId/claims", element: <LazyRoute><ResumeClaimsPage /></LazyRoute> },
      { path: "interviews", element: <LazyRoute><InterviewListPage /></LazyRoute> },
      { path: "interviews/new", element: <LazyRoute><InterviewCreatePage /></LazyRoute> },
      { path: "interviews/:interviewId/report", element: <LazyRoute><InterviewReportPage /></LazyRoute> },
      { path: "analytics", element: <LazyRoute><AnalyticsPage /></LazyRoute> },
      { path: "settings", element: <LazyRoute><SettingsPage /></LazyRoute> },
    ],
  },
  {
    path: "/app/interviews/:interviewId/live",
    element: <InterviewLayout />,
    children: [{ index: true, element: <LazyRoute><InterviewRoomPage /></LazyRoute> }],
  },
  { path: "/", element: <Navigate to="/app/dashboard" replace /> },
  { path: "*", element: <NotFoundPage /> },
])
