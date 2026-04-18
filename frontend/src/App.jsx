import { BrowserRouter, Routes, Route } from "react-router-dom"
import Navbar from "./components/Navbar"
import Upload from "./pages/Upload"
import Audit from "./pages/Audit"
import Remediate from "./pages/Remediate"

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ minHeight: "100vh", background: "#0f1117", color: "#e8eaf0" }}>
        <Navbar />
        <Routes>
          <Route path="/" element={<Upload />} />
          <Route path="/audit" element={<Audit />} />
          <Route path="/remediate" element={<Remediate />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}