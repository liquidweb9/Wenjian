import { lazy, Suspense } from "react"
import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout } from "@/components/layout/AppLayout"
import { InterviewLayout } from "@/components/layout/InterviewLayout"
import { ProtectedRoute, PublicOnlyRoute } from "@/features/auth/components/protected-route"

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
const RegisterPage = lazy(() => import("@/features/auth/pages/register-page"))
const JobTargetListPage = lazy(() => import("@/features/job-target/pages/job-target-list-page"))
const JobTargetCreatePage = lazy(() => import("@/features/job-target/pages/job-target-create-page"))
const JobTargetDetailPage = lazy(() => import("@/features/job-target/pages/job-target-detail-page"))
const ClaimGapPage = lazy(() => import("@/features/claim-gap/pages/claim-gap-page"))
const AbilityProfilePage = lazy(() => import("@/features/ability-profile/pages/ability-profile-page"))
const TrainingPlanPage = lazy(() => import("@/features/training-plan/pages/training-plan-page"))
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
  // Public-only routes (redirect to dashboard if authenticated)
  {
    path: "/login",
    element: (
      <PublicOnlyRoute>
        <LazyRoute>
          <LoginPage />
        </LazyRoute>
      </PublicOnlyRoute>
    ),
  },
  {
    path: "/register",
    element: (
      <PublicOnlyRoute>
        <LazyRoute>
          <RegisterPage />
        </LazyRoute>
      </PublicOnlyRoute>
    ),
  },
  // Protected routes (require authentication)
  {
    path: "/app",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="dashboard" replace /> },
      { path: "dashboard", element: <LazyRoute><DashboardPage /></LazyRoute> },
      { path: "resumes", element: <LazyRoute><ResumeListPage /></LazyRoute> },
      { path: "resumes/new", element: <LazyRoute><ResumeUploadPage /></LazyRoute> },
      { path: "resumes/:resumeId/review", element: <LazyRoute><ResumeReviewPage /></LazyRoute> },
      { path: "resumes/:resumeId/profile", element: <LazyRoute><ResumeProfilePage /></LazyRoute> },
      { path: "resumes/:resumeId/claims", element: <LazyRoute><ResumeClaimsPage /></LazyRoute> },
      { path: "resumes/:resumeId/ability-profile", element: <LazyRoute><AbilityProfilePage /></LazyRoute> },
      { path: "resumes/:resumeId/training-plan", element: <LazyRoute><TrainingPlanPage /></LazyRoute> },
      { path: "interviews", element: <LazyRoute><InterviewListPage /></LazyRoute> },
      { path: "interviews/new", element: <LazyRoute><InterviewCreatePage /></LazyRoute> },
      { path: "interviews/:interviewId/report", element: <LazyRoute><InterviewReportPage /></LazyRoute> },
      { path: "job-targets", element: <LazyRoute><JobTargetListPage /></LazyRoute> },
      { path: "job-targets/create", element: <LazyRoute><JobTargetCreatePage /></LazyRoute> },
      { path: "job-targets/:jobTargetId", element: <LazyRoute><JobTargetDetailPage /></LazyRoute> },
      { path: "claim-gap/:resumeId/:jobTargetId", element: <LazyRoute><ClaimGapPage /></LazyRoute> },
      { path: "analytics", element: <LazyRoute><AnalyticsPage /></LazyRoute> },
      { path: "settings", element: <LazyRoute><SettingsPage /></LazyRoute> },
    ],
  },
  {
    path: "/app/interviews/:interviewId/live",
    element: (
      <ProtectedRoute>
        <InterviewLayout />
      </ProtectedRoute>
    ),
    children: [{ index: true, element: <LazyRoute><InterviewRoomPage /></LazyRoute> }],
  },
  // Root redirect
  { path: "/", element: <Navigate to="/login" replace /> },
  { path: "*", element: <NotFoundPage /> },
])
