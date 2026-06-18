import { motion } from 'framer-motion'
import clsx from 'clsx'

export function StorageUsageWidget({ storage }) {
  if (!storage) {
    return (
      <div className="rounded-2xl border border-slate-200/75 bg-white/80 p-4">
        <p className="text-sm text-slate-500">Loading storage usage...</p>
      </div>
    )
  }

  const percent = Math.min(storage.percent_used, 100)
  const isNearLimit = percent >= 85

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-2xl border border-slate-200/75 bg-white/80 p-5 backdrop-blur"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-900">Storage usage</p>
          <p className="mt-1 text-xs text-slate-500">
            {storage.used_display} of {storage.quota_display} used
          </p>
        </div>
        <p className="text-sm font-semibold text-indigo-600">{percent}%</p>
      </div>

      <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-slate-100">
        <motion.div
          className={clsx(
            'h-full rounded-full',
            isNearLimit
              ? 'bg-gradient-to-r from-amber-500 to-rose-500'
              : 'bg-gradient-to-r from-indigo-500 to-violet-500',
          )}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        />
      </div>

      <p className="mt-3 text-xs text-slate-500">
        {storage.remaining_display} remaining
      </p>
    </motion.div>
  )
}
