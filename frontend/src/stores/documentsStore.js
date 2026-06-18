import { create } from 'zustand'
import { api } from '../lib/api'
import { parseApiError } from '../lib/parseApiError'

export const ALLOWED_EXTENSIONS = ['pdf', 'pptx', 'docx', 'txt', 'md']

export const useDocumentsStore = create((set, get) => ({
  documents: [],
  storage: null,
  selectedDocument: null,
  loading: false,
  uploading: false,
  uploadProgress: 0,
  error: null,
  successMessage: null,

  clearMessages: () => set({ error: null, successMessage: null }),

  fetchDocuments: async (workspaceId, sort = 'date') => {
    try {
      set({ loading: true, error: null })
      const response = await api.get(`/workspaces/${workspaceId}/documents/`, {
        params: { sort },
      })
      set({ documents: response.data, loading: false })
    } catch (error) {
      set({
        loading: false,
        error: parseApiError(error, 'Could not load documents.'),
      })
    }
  },

  fetchStorage: async () => {
    try {
      const response = await api.get('/storage/')
      set({ storage: response.data })
    } catch (error) {
      set({ error: parseApiError(error, 'Could not load storage usage.') })
    }
  },

  uploadDocument: async (workspaceId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('workspace_id', workspaceId)

    set({
      uploading: true,
      uploadProgress: 0,
      error: null,
      successMessage: null,
    })

    try {
      const response = await api.post('/documents/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (!event.total) {
            return
          }
          const percent = Math.round((event.loaded * 100) / event.total)
          set({ uploadProgress: percent })
        },
      })

      set((state) => ({
        documents: [response.data, ...state.documents],
        uploading: false,
        uploadProgress: 100,
        successMessage: `"${file.name}" uploaded successfully.`,
      }))

      await get().fetchStorage()
      return { success: true, document: response.data }
    } catch (error) {
      const message = parseApiError(error, 'Upload failed.')
      set({
        uploading: false,
        uploadProgress: 0,
        error: message,
      })
      return { success: false, message }
    }
  },

  fetchDocumentDetail: async (documentId) => {
    try {
      const response = await api.get(`/documents/${documentId}/`)
      set({ selectedDocument: response.data })
      return { success: true, document: response.data }
    } catch (error) {
      const message = parseApiError(error, 'Could not load document metadata.')
      set({ error: message })
      return { success: false, message }
    }
  },

  deleteDocument: async (documentId) => {
    try {
      await api.delete(`/documents/${documentId}/delete/`)
      set((state) => ({
        documents: state.documents.filter((document) => document.id !== documentId),
        selectedDocument:
          state.selectedDocument?.id === documentId ? null : state.selectedDocument,
        successMessage: 'Document deleted successfully.',
      }))
      await get().fetchStorage()
      return { success: true }
    } catch (error) {
      const message = parseApiError(error, 'Delete failed.')
      set({ error: message })
      return { success: false, message }
    }
  },

  clearSelectedDocument: () => set({ selectedDocument: null }),

  clear: () =>
    set({
      documents: [],
      storage: null,
      selectedDocument: null,
      loading: false,
      uploading: false,
      uploadProgress: 0,
      error: null,
      successMessage: null,
    }),
}))
