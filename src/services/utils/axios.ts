import axios from "axios";

const apiClient = axios.create({
  baseURL: `${import.meta.env.BASE_SERVER_URL}/api/v1`,
  headers: {
    "Accept": "application/json",
    "Content-Type": "application/json"
  }
});

export default apiClient;