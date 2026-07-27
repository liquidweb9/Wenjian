import { Outlet } from "react-router-dom"
import { Sidebar } from "./Sidebar"
import { Topbar } from "./Topbar"

export function AppLayout() {
  return (
    <div style={{ display: "flex", height: "100dvh", overflow: "hidden" }}>
      <Sidebar />
      <div style={{ flex: 1, minWidth: 0, minHeight: 0, display: "flex", flexDirection: "column" }}>
        <Topbar />
        <main
          style={{
            flex: 1,
            minHeight: 0,
            overflow: "auto",
            padding: "1.5rem",
            background: "transparent",
          }}
        >
          <div style={{ maxWidth: 1440, margin: "0 auto" }}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
