import { defineStore } from 'pinia'
import axios from 'axios'
import type { AdminUser } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('admin_access_token'),
    refreshToken: localStorage.getItem('admin_refresh_token'),
    user: null as AdminUser | null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.accessToken,
    permissions: (state) => new Set(state.user?.permissions ?? []),
  },
  actions: {
    setTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken
      localStorage.setItem('admin_access_token', accessToken)
      localStorage.setItem('admin_refresh_token', refreshToken)
    },
    async login(email: string, password: string) {
      const { data } = await axios.post(`${API_BASE_URL}/api/v1/admin/auth/login`, {
        email,
        password,
      })
      this.setTokens(data.access_token, data.refresh_token)
      await this.fetchMe()
    },
    async fetchMe() {
      const { data } = await axios.get<AdminUser>(`${API_BASE_URL}/api/v1/admin/auth/me`, {
        headers: { Authorization: `Bearer ${this.accessToken}` },
      })
      this.user = data
    },
    async refreshAccessToken(): Promise<string | null> {
      if (!this.refreshToken) return null
      try {
        const { data } = await axios.post(`${API_BASE_URL}/api/v1/admin/auth/refresh`, {
          refresh_token: this.refreshToken,
        })
        this.setTokens(data.access_token, data.refresh_token)
        return data.access_token
      } catch {
        return null
      }
    },
    logout() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem('admin_access_token')
      localStorage.removeItem('admin_refresh_token')
    },
  },
})
