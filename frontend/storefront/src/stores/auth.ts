import { defineStore } from 'pinia'
import axios from 'axios'

interface Customer {
  id: number
  email: string
  full_name: string | null
  phone: string | null
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('storefront_access_token'),
    refreshToken: localStorage.getItem('storefront_refresh_token'),
    customer: null as Customer | null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.accessToken,
  },
  actions: {
    setTokens(accessToken: string, refreshToken: string) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken
      localStorage.setItem('storefront_access_token', accessToken)
      localStorage.setItem('storefront_refresh_token', refreshToken)
    },
    async login(email: string, password: string) {
      const { data } = await axios.post(`${API_BASE_URL}/api/v1/storefront/auth/login`, {
        email,
        password,
      })
      this.setTokens(data.access_token, data.refresh_token)
    },
    async register(email: string, password: string, fullName: string) {
      await axios.post(`${API_BASE_URL}/api/v1/storefront/auth/register`, {
        email,
        password,
        full_name: fullName,
      })
    },
    async refreshAccessToken(): Promise<string | null> {
      if (!this.refreshToken) return null
      try {
        const { data } = await axios.post(`${API_BASE_URL}/api/v1/storefront/auth/refresh`, {
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
      this.customer = null
      localStorage.removeItem('storefront_access_token')
      localStorage.removeItem('storefront_refresh_token')
    },
  },
})
