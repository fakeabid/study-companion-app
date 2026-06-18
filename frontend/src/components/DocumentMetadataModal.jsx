import { motion } from 'framer-motion'
import { formatBytes, formatDate } from '../lib/format'

export function DocumentMetadataModal({ document, loading, onClose }) {
  if (!document && !loading) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <motion.button
        type="button"
        aria-label="Close metadata modal"
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />

      <motion.div
        role="dialog"
        aria-modal="true"
        aria-labelledby="metadata-title"
        initial={{ opacity: 0, scale: 0.96, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 12 }}
        transition={{ duration: 0.2 }}
        className="relative z-10 w-full max-w-lg rounded-3xl border border-white/80 bg-white p-6 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-indigo-500">
              Document metadata
            </p>
            <h2 id="metadata-title" className="mt-2 text-xl font-semibold text-slate-900">
              {loading ? 'Loading...' : document.original_filename}
            </h2>
          </div>
          <button type="button" onClick={onClose} className="btn-ghost">
            Close
          </button>
        </div>

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Fetching document details...</p>
        ) : (
          <dl className="mt-6 space-y-3 text-sm">
            <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
              <dt className="text-slate-500">File type</dt>
              <dd className="font-medium uppercase text-slate-900">{document.file_type}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
              <dt className="text-slate-500">Size</dt>
              <dd className="font-medium text-slate-900">{formatBytes(document.file_size)}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
              <dt className="text-slate-500">Uploaded at</dt>
              <dd className="font-medium text-slate-900">{formatDate(document.uploaded_at)}</dd>
            </div>
            <div className="flex justify-between gap-4 border-b border-slate-100 pb-2">
              <dt className="text-slate-500">Workspace</dt>
              <dd className="font-medium text-slate-900">{document.workspace_name}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">Uploaded by</dt>
              <dd className="font-medium text-slate-900">{document.uploaded_by_email}</dd>
            </div>
          </dl>
        )}
      </motion.div>
    </div>
  )
}
