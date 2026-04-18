import { Link, useLocation } from "react-router-dom"

export default function Navbar() {
  const { pathname } = useLocation()
  const links = [
    { to: "/", label: "Upload" },
    { to: "/audit", label: "Audit" },
    { to: "/remediate", label: "Remediate" }
  ]

  return (
    <nav style={{
      display: "flex", alignItems: "center", gap: "32px",
      padding: "16px 40px", borderBottom: "1px solid #1e2130",
      background: "#0a0d14"
    }}>
      <span style={{ fontWeight: 700, fontSize: 20, color: "#4ade80", letterSpacing: -0.5 }}>
        FairLens
      </span>
      {links.map(l => (
        <Link key={l.to} to={l.to} style={{
          color: pathname === l.to ? "#4ade80" : "#8b92a5",
          textDecoration: "none", fontSize: 14, fontWeight: 500,
          borderBottom: pathname === l.to ? "2px solid #4ade80" : "2px solid transparent",
          paddingBottom: 2
        }}>{l.label}</Link>
      ))}
    </nav>
  )
}