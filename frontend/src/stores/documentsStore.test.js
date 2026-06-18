import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import MockAdapter from 'axios-mock-adapter'
import { api } from '../lib/api'
import { useAuthStore } from './authStore'
import { useDocumentsStore } from './documentsStore'

const WORKSPACE_ID = '11111111-1111-1111-1111-111111111111'
const OTHER_WORKSPACE_ID = '22222222-2222-2222-2222-222222222222'
const DOCUMENT_ID = '33333333-3333-3333-3333-333333333333'

const sampleDocument = {
  id: DOCUMENT_ID,
  original_filename: 'lecture.pdf',
  file_type: 'pdf',
  file_size: 2048,
  uploaded_at: '2026-06-18T10:00:00Z',
  workspace_id: WORKSPACE_ID,
  workspace_name: 'ML',
  uploaded_by_email: 'alice@example.com',
}

const emptyStorage = {
  used_bytes: 0,
  used_display: '0 B',
  remaining_bytes: 1073741824,
  remaining_display: '1.0 GB',
  quota_bytes: 1073741824,
  quota_display: '1.0 GB',
  percent_used: 0,
}

const usedStorage = {
  used_bytes: 2048,
  used_display: '2.0 KB',
  remaining_bytes: 1073739776,
  remaining_display: '1.0 GB',
  quota_bytes: 1073741824,
  quota_display: '1.0 GB',
  percent_used: 0,
}

describe('documentsStore', () => {
  let mock

  beforeEach(() => {
    mock = new MockAdapter(api)
    useAuthStore.setState({
      accessToken: 'test-access-token',
      refreshToken: 'test-refresh-token',
    })
    useDocumentsStore.getState().clear()
  })

  afterEach(() => {
    mock.restore()
  })

  describe('upload', () => {
    it('uploads a valid file successfully', async () => {
      mock.onGet('/storage/').reply(200, emptyStorage)
      mock.onPost('/documents/upload/').reply(201, sampleDocument)

      const file = new File(['pdf-content'], 'lecture.pdf', { type: 'application/pdf' })
      const result = await useDocumentsStore.getState().uploadDocument(WORKSPACE_ID, file)

      expect(result.success).toBe(true)
      expect(useDocumentsStore.getState().documents).toHaveLength(1)
      expect(useDocumentsStore.getState().successMessage).toContain('lecture.pdf')
    })

    it('returns an error for invalid file type', async () => {
      mock.onPost('/documents/upload/').reply(400, {
        file: ["Unsupported file type '.mp4'. Allowed types: DOCX, MD, PDF, PPTX, TXT."],
      })

      const file = new File(['video'], 'video.mp4', { type: 'video/mp4' })
      const result = await useDocumentsStore.getState().uploadDocument(WORKSPACE_ID, file)

      expect(result.success).toBe(false)
      expect(result.message).toContain('Unsupported file type')
      expect(useDocumentsStore.getState().error).toContain('Unsupported file type')
    })

    it('returns an error when quota is exceeded', async () => {
      mock.onPost('/documents/upload/').reply(400, {
        file: ['Storage quota exceeded. File size: 2.0 KB. Remaining storage: 0 B.'],
      })

      const file = new File(['x'.repeat(2048)], 'big.pdf', { type: 'application/pdf' })
      const result = await useDocumentsStore.getState().uploadDocument(WORKSPACE_ID, file)

      expect(result.success).toBe(false)
      expect(result.message.toLowerCase()).toContain('quota')
    })

    it('fails upload when unauthorized', async () => {
      useAuthStore.setState({ accessToken: null, refreshToken: null })
      mock.onPost('/documents/upload/').reply(401, { detail: 'Authentication credentials were not provided.' })

      const file = new File(['pdf'], 'lecture.pdf', { type: 'application/pdf' })
      const result = await useDocumentsStore.getState().uploadDocument(WORKSPACE_ID, file)

      expect(result.success).toBe(false)
    })
  })

  describe('documents', () => {
    it('lists documents for a workspace', async () => {
      mock.onGet(`/workspaces/${WORKSPACE_ID}/documents/`).reply(200, [sampleDocument])

      await useDocumentsStore.getState().fetchDocuments(WORKSPACE_ID)

      expect(useDocumentsStore.getState().documents).toHaveLength(1)
      expect(useDocumentsStore.getState().documents[0].original_filename).toBe('lecture.pdf')
    })

    it('loads document metadata', async () => {
      mock.onGet(`/documents/${DOCUMENT_ID}/`).reply(200, sampleDocument)

      const result = await useDocumentsStore.getState().fetchDocumentDetail(DOCUMENT_ID)

      expect(result.success).toBe(true)
      expect(useDocumentsStore.getState().selectedDocument.workspace_name).toBe('ML')
      expect(useDocumentsStore.getState().selectedDocument.uploaded_by_email).toBe('alice@example.com')
    })

    it('deletes a document', async () => {
      useDocumentsStore.setState({ documents: [sampleDocument] })
      mock.onDelete(`/documents/${DOCUMENT_ID}/delete/`).reply(204)
      mock.onGet('/storage/').reply(200, emptyStorage)

      const result = await useDocumentsStore.getState().deleteDocument(DOCUMENT_ID)

      expect(result.success).toBe(true)
      expect(useDocumentsStore.getState().documents).toHaveLength(0)
      expect(useDocumentsStore.getState().successMessage).toContain('deleted')
    })
  })

  describe('permissions', () => {
    it('cannot view another user document metadata', async () => {
      mock.onGet(`/documents/${DOCUMENT_ID}/`).reply(404, { detail: 'Not found.' })

      const result = await useDocumentsStore.getState().fetchDocumentDetail(DOCUMENT_ID)

      expect(result.success).toBe(false)
      expect(useDocumentsStore.getState().error).toBeTruthy()
    })

    it('cannot upload into another user workspace', async () => {
      mock.onPost('/documents/upload/').reply(403, {
        detail: 'You do not have access to this workspace.',
      })

      const file = new File(['pdf'], 'lecture.pdf', { type: 'application/pdf' })
      const result = await useDocumentsStore
        .getState()
        .uploadDocument(OTHER_WORKSPACE_ID, file)

      expect(result.success).toBe(false)
      expect(result.message).toContain('access')
    })
  })

  describe('storage', () => {
    it('updates storage after upload', async () => {
      mock.onPost('/documents/upload/').reply(201, sampleDocument)
      mock.onGet('/storage/').reply(200, usedStorage)

      const file = new File(['pdf'], 'lecture.pdf', { type: 'application/pdf' })
      await useDocumentsStore.getState().uploadDocument(WORKSPACE_ID, file)

      expect(useDocumentsStore.getState().storage.used_bytes).toBe(2048)
      expect(useDocumentsStore.getState().storage.percent_used).toBe(0)
    })

    it('updates storage after delete', async () => {
      useDocumentsStore.setState({ documents: [sampleDocument], storage: usedStorage })
      mock.onDelete(`/documents/${DOCUMENT_ID}/delete/`).reply(204)
      mock.onGet('/storage/').reply(200, emptyStorage)

      await useDocumentsStore.getState().deleteDocument(DOCUMENT_ID)

      expect(useDocumentsStore.getState().storage.used_bytes).toBe(0)
      expect(useDocumentsStore.getState().storage.remaining_bytes).toBe(1073741824)
    })
  })
})
