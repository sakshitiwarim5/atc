import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000", // ✅ FastAPI backend ka base URL
});

export default api;
