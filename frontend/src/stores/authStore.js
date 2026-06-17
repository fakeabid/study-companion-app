import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../lib/api'

const parseApiError = (error) => {
  const payload = error?.response?.data

  if (typeof payload === 'string') {
    return payload
  }

  if (payload?.detail) {
    return payload.detail
  }

  if (payload && typeof payload === 'object') {
    const firstValue = Object.values(payload)[0]
    if (Array.isArray(firstValue)) {
      return firstValue[0]
    }
  }

  return 'Something went wrong. Please try again.'
}

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      status: 'idle',
      setStatus: (status) => set({ status }),
      setTokens: (accessToken, refreshToken) =>
        set({
          accessToken,
          refreshToken,
        }),
      clearSession: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          status: 'idle',
        }),
      register: async (payload) => {
        try {
          set({ status: 'loading' })
          await api.post('/auth/register/', payload)
          const loginResponse = await api.post('/auth/login/', {
            email: payload.email,
            password: payload.password,
          })
          const { access, refresh } = loginResponse.data
          get().setTokens(access, refresh)
          await get().fetchMe()
          set({ status: 'success' })
          return { success: true }
        } catch (error) {
          set({ status: 'error' })
          return { success: false, message: parseApiError(error) }
        }
      },
      login: async (payload) => {
        try {
          set({ status: 'loading' })
          const response = await api.post('/auth/login/', payload)
          const { access, refresh } = response.data
          get().setTokens(access, refresh)
          await get().fetchMe()
          set({ status: 'success' })
          return { success: true }
        } catch (error) {
          set({ status: 'error' })
          return { success: false, message: parseApiError(error) }
        }
      },
      fetchMe: async () => {
        const { accessToken } = get()
        if (!accessToken) {
          return
        }

        try {
          const response = await api.get('/auth/me/')
          set({ user: response.data })
        } catch {
          get().clearSession()
        }
      },
      logout: () => {
        get().clearSession()
      },
    }),
    {
      name: 'notesly-auth',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    },
  ),
)
