import axios from 'axios'
import { useAuthStore } from '../stores/auth'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
})

apiClient.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

let refreshPromise: Promise<string | null> | null = null

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    const originalRequest = error.config

    if (error.response?.status === 401 && auth.refreshToken && !originalRequest._retried) {
      originalRequest._retried = true
      refreshPromise ??= auth.refreshAccessToken()
      const newAccessToken = await refreshPromise
      refreshPromise = null

      if (newAccessToken) {
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      }
      auth.logout()
    }

    return Promise.reject(error)
  },
)

export function imageUrl(storageKey: string): string {
  const uploadsBase = import.meta.env.VITE_UPLOADS_BASE_URL
  if (uploadsBase) return `${uploadsBase}/${storageKey}`
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  return `${base}/uploads/${storageKey}`
}
