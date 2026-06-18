import { useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import clsx from 'clsx'
import { ALLOWED_EXTENSIONS } from '../stores/documentsStore'

const ACCEPT = ALLOWED_EXTENSIONS.map((ext) => `.${ext}`).join(',')

export function FileUploadZone({ onUpload, uploading, uploadProgress, error, successMessage }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = async (fileList) => {
    const file = fileList?.[0]
    if (!file || uploading) {
      return
    }
    await onUpload(file)
  }

  const onDrop = async (event) => {
    event.preventDefault()
    setIsDragging(false)
    await handleFiles(event.dataTransfer.files)
  }

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            inputRef.current?.click()
          }
        }}
        onDragEnter={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={(event) => {
          event.preventDefault()
          setIsDragging(false)
        }}
        onDrop={onDrop}
        className={clsx(
          'rounded-2xl border-2 border-dashed p-8 text-center transition',
          isDragging
            ? 'border-indigo-400 bg-indigo-50/70'
            : 'border-slate-300 bg-white/70 hover:border-indigo-300 hover:bg-indigo-50/40',
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(event) => handleFiles(event.target.files)}
        />

        <motion.div
          animate={{ scale: isDragging ? 1.02 : 1 }}
          transition={{ duration: 0.2 }}
        >
          <p className="text-base font-medium text-slate-900">
            Drag and drop a document here
          </p>
          <p className="mt-2 text-sm text-slate-500">
            or use the file picker below
          </p>
          <p className="mt-3 text-xs text-slate-400">
            Supported: {ALLOWED_EXTENSIONS.join(', ').toUpperCase()}
          </p>

          <button
            type="button"
            disabled={uploading}
            onClick={() => inputRef.current?.click()}
            className="btn-primary mt-5 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {uploading ? 'Uploading...' : 'Choose file'}
          </button>
        </motion.div>
      </div>

      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3"
          >
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-medium text-indigo-700">Uploading...</span>
              <span className="text-indigo-600">{uploadProgress}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-indigo-100">
              <motion.div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500"
                initial={{ width: 0 }}
                animate={{ width: `${uploadProgress}%` }}
                transition={{ duration: 0.2 }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {successMessage && !uploading && (
          <motion.p
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700"
          >
            {successMessage}
          </motion.p>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && !uploading && (
          <motion.p
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}
