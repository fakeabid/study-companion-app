import { motion } from 'framer-motion'
import { formatBytes, formatDate } from '../lib/format'

const typeColors = {
  pdf: 'bg-rose-100 text-rose-700',
  docx: 'bg-blue-100 text-blue-700',
  pptx: 'bg-orange-100 text-orange-700',
  txt: 'bg-slate-100 text-slate-700',
  md: 'bg-violet-100 text-violet-700',
}

export function DocumentCard({ document, onViewMetadata, onDelete, deleting }) {
  const badgeClass = typeColors[document.file_type] ?? 'bg-slate-100 text-slate-700'

  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -12 }}
      transition={{ duration: 0.2 }}
      className="rounded-2xl border border-slate-200/75 bg-white/80 p-4 backdrop-blur"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate font-medium text-slate-900">
              {document.original_filename}
            </h3>
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold uppercase ${badgeClass}`}>
              {document.file_type}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
            <span>{formatBytes(document.file_size)}</span>
            <span>Uploaded {formatDate(document.uploaded_at)}</span>
          </div>
        </div>

        <div className="flex gap-2">
          <button type="button" className="btn-ghost" onClick={() => onViewMetadata(document.id)}>
            View metadata
          </button>
          <button
            type="button"
            disabled={deleting}
            onClick={() => onDelete(document.id)}
            className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-100 disabled:opacity-60"
          >
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
        </div>
      </div>
    </motion.article>
  )
}
