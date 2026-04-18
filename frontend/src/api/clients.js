import axios from "axios"

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"
})

export const uploadDataset = (file) => {
  const form = new FormData()
  form.append("file", file)
  return API.post("/ingest/", form)
}

export const runFullAudit = (dataset_id, protected_columns, target_column) =>
  API.post("/audit/full", { dataset_id, protected_columns, target_column })

export const runRemediation = (dataset_id, protected_column, target_column) =>
  API.post("/remediate/", { dataset_id, protected_column, target_column })