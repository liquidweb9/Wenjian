import { Link } from "react-router-dom"
import { BrandMark } from "@/components/brand/BrandLogo"

export default function NotFoundPage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "2rem",
      }}
    >
      <section className="app-surface" style={{ maxWidth: 560, padding: "2.8rem 2rem", textAlign: "center" }}>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <BrandMark size={48} />
        </div>
        <div className="app-eyebrow" style={{ justifyContent: "center", marginTop: "1rem" }}>
          404
        </div>
        <h1 style={{ margin: "0.5rem 0 0", fontSize: "1.45rem", fontWeight: 600, color: "var(--wj-text-primary)" }}>
          这个页面没有被问到
        </h1>
        <p style={{ margin: "0.65rem auto 0", maxWidth: 380, color: "var(--wj-text-secondary)", lineHeight: 1.7 }}>
          你访问的内容不存在，或者已经被移动。回到工作台后，可以继续当前训练或重新开始。
        </p>
        <Link to="/app/dashboard" className="btn-primary" style={{ marginTop: "1.5rem" }}>
          返回工作台
        </Link>
      </section>
    </div>
  )
}
