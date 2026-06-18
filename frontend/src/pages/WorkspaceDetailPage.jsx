import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { DocumentCard } from '../components/DocumentCard'
import { DocumentMetadataModal } from '../components/DocumentMetadataModal'
import { FileUploadZone } from '../components/FileUploadZone'
import { StorageUsageWidget } from '../components/StorageUsageWidget'
import { useDocumentsStore } from '../stores/documentsStore'
import { useWorkspacesStore } from '../stores/workspacesStore'

export function WorkspaceDetailPage() {
  const { workspaceId } = useParams()
  const navigate = useNavigate()
  const { workspaces, fetchWorkspaces, loading: workspacesLoading } = useWorkspacesStore()
  const {
    documents,
    storage,
    selectedDocument,
    loading,
    uploading,
    uploadProgress,
    error,
    successMessage,
    fetchDocuments,
    fetchStorage,
    uploadDocument,
    fetchDocumentDetail,
    deleteDocument,
    clearSelectedDocument,
    clearMessages,
    clear,
  } = useDocumentsStore()

  const [sort, setSort] = useState('date')
  const [metadataLoading, setMetadataLoading] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  const workspace = useMemo(
    () => workspaces.find((item) => item.id === workspaceId),
    [workspaces, workspaceId],
  )

  useEffect(() => {
    fetchWorkspaces()
    fetchStorage()

    return () => {
      clear()
    }
  }, [workspaceId, fetchWorkspaces, fetchStorage, clear])

  useEffect(() => {
    fetchDocuments(workspaceId, sort)
  }, [workspaceId, sort, fetchDocuments])

  useEffect(() => {
    if (!workspacesLoading && workspaces.length > 0 && !workspace) {
      navigate('/dashboard', { replace: true })
    }
  }, [workspacesLoading, workspaces, workspace, navigate])

  const handleUpload = async (file) => {
    clearMessages()
    await uploadDocument(workspaceId, file)
  }

  const handleViewMetadata = async (documentId) => {
    setMetadataLoading(true)
    clearMessages()
    await fetchDocumentDetail(documentId)
    setMetadataLoading(false)
  }

  const handleDelete = async (documentId) => {
    setDeletingId(documentId)
    clearMessages()
    await deleteDocument(documentId)
    setDeletingId(null)
  }

  return (
    <div className="relative z-10 mx-auto min-h-screen w-full max-w-5xl px-4 py-8 md:px-10 md:py-12">
      <motion.header
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="glass-panel mb-8 p-6"
      >
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <Link
              to="/dashboard"
              className="text-sm font-medium text-indigo-600 transition hover:text-indigo-700"
            >
              ← Back to workspaces
            </Link>
            <p className="mt-3 text-xs font-semibold uppercase tracking-widest text-indigo-500">
              notesly.ai
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-slate-900 md:text-3xl">
              {workspace?.name ?? 'Workspace'}
            </h1>
          </div>
        </div>
      </motion.header>

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <motion.section
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.05 }}
          className="glass-panel p-5 md:p-6"
        >
          <h2 className="text-lg font-semibold text-slate-900">Upload document</h2>
          <p className="mt-1 text-sm text-slate-500">
            Drag and drop or pick a file to add it to this workspace.
          </p>
          <div className="mt-5">
            <FileUploadZone
              onUpload={handleUpload}
              uploading={uploading}
              uploadProgress={uploadProgress}
              error={error}
              successMessage={successMessage}
            />
          </div>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1 }}
        >
          <StorageUsageWidget storage={storage} />
        </motion.section>
      </div>

      <motion.section
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.15 }}
        className="glass-panel mt-6 p-5 md:p-6"
      >
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Documents</h2>
            <p className="mt-1 text-sm text-slate-500">
              {documents.length} file{documents.length === 1 ? '' : 's'} in this workspace
            </p>
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-600">
            Sort by
            <select
              className="input w-auto py-2"
              value={sort}
              onChange={(event) => setSort(event.target.value)}
            >
              <option value="date">Date (newest)</option>
              <option value="name">Name</option>
              <option value="size">Size</option>
            </select>
          </label>
        </div>

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Loading documents...</p>
        ) : (
          <div className="mt-6 space-y-3">
            <AnimatePresence mode="popLayout">
              {documents.map((document) => (
                <DocumentCard
                  key={document.id}
                  document={document}
                  deleting={deletingId === document.id}
                  onViewMetadata={handleViewMetadata}
                  onDelete={handleDelete}
                />
              ))}
            </AnimatePresence>
            {!documents.length && (
              <p className="rounded-xl border border-dashed border-slate-300 px-4 py-8 text-center text-slate-500">
                No documents yet. Upload your first file to get started.
              </p>
            )}
          </div>
        )}
      </motion.section>

      <AnimatePresence>
        {(selectedDocument || metadataLoading) && (
          <DocumentMetadataModal
            document={selectedDocument}
            loading={metadataLoading}
            onClose={clearSelectedDocument}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
