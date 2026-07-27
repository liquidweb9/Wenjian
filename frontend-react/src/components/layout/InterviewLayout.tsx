import { Outlet } from "react-router-dom"

export function InterviewLayout() {
  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <Outlet />
    </div>
  )
}
