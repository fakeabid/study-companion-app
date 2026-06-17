import { create } from 'zustand'
import { api } from '../lib/api'

const parseApiError = (error, fallback) => {
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

  return fallback
}

export const useWorkspacesStore = create((set) => ({
  workspaces: [],
  loading: false,
  error: null,
  fetchWorkspaces: async () => {
    try {
      set({ loading: true, error: null })
      const response = await api.get('/workspaces/')
      set({ workspaces: response.data, loading: false })
    } catch (error) {
      set({
        loading: false,
        error: parseApiError(error, 'Could not load workspaces.'),
      })
    }
  },
  createWorkspace: async (name) => {
    try {
      const response = await api.post('/workspaces/', { name })
      set((state) => ({
        workspaces: [response.data, ...state.workspaces],
      }))
      return { success: true }
    } catch (error) {
      return { success: false, message: parseApiError(error, 'Creation failed.') }
    }
  },
  renameWorkspace: async (id, name) => {
    try {
      const response = await api.patch(`/workspaces/${id}/`, { name })
      set((state) => ({
        workspaces: state.workspaces.map((workspace) =>
          workspace.id === id ? response.data : workspace,
        ),
      }))
      return { success: true }
    } catch (error) {
      return { success: false, message: parseApiError(error, 'Rename failed.') }
    }
  },
  deleteWorkspace: async (id) => {
    try {
      await api.delete(`/workspaces/${id}/`)
      set((state) => ({
        workspaces: state.workspaces.filter((workspace) => workspace.id !== id),
      }))
      return { success: true }
    } catch (error) {
      return { success: false, message: parseApiError(error, 'Delete failed.') }
    }
  },
  clear: () => set({ workspaces: [], error: null, loading: false }),
}))
