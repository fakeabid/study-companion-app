import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useAuthStore } from '../stores/authStore'
import { useWorkspacesStore } from '../stores/workspacesStore'

const formatDate = (isoDate) =>
  new Date(isoDate).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

export function DashboardPage() {
  const { user, logout } = useAuthStore()
  const {
    workspaces,
    loading,
    error,
    fetchWorkspaces,
    createWorkspace,
    renameWorkspace,
    deleteWorkspace,
    clear,
  } = useWorkspacesStore()

  const [name, setName] = useState('')
  const [activeId, setActiveId] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    fetchWorkspaces()
  }, [fetchWorkspaces])

  const firstName = useMemo(() => user?.first_name ?? 'there', [user?.first_name])

  const onCreate = async (event) => {
    event.preventDefault()
    setMessage('')
    const trimmed = name.trim()
    if (!trimmed) {
      setMessage('Workspace name cannot be empty.')
      return
    }

    const result = await createWorkspace(trimmed)
    if (!result.success) {
      setMessage(result.message)
      return
    }

    setName('')
  }

  const onRename = async (id) => {
    const trimmed = renameValue.trim()
    if (!trimmed) {
      setMessage('Workspace name cannot be empty.')
      return
    }

    const result = await renameWorkspace(id, trimmed)
    if (!result.success) {
      setMessage(result.message)
      return
    }

    setActiveId(null)
    setRenameValue('')
  }

  const handleLogout = () => {
    clear()
    logout()
  }

  return (
    <div className="relative z-10 mx-auto min-h-screen w-full max-w-5xl px-4 py-8 md:px-10 md:py-12">
      <motion.header
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45 }}
        className="glass-panel mb-8 flex flex-col gap-4 p-6 md:flex-row md:items-center md:justify-between"
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-indigo-500">
            notesly.ai
          </p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-900 md:text-3xl">
            Hi {firstName}, your workspaces
          </h1>
        </div>
        <button type="button" onClick={handleLogout} className="btn-ghost">
          Logout
        </button>
      </motion.header>

      <motion.section
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.1 }}
        className="glass-panel p-5 md:p-6"
      >
        <form onSubmit={onCreate} className="flex flex-col gap-3 md:flex-row">
          <input
            className="input flex-1"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Create a new workspace..."
            maxLength={255}
          />
          <button type="submit" className="btn-primary md:w-44">
            Add workspace
          </button>
        </form>

        {(error || message) && (
          <p className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error || message}
          </p>
        )}

        {loading ? (
          <p className="mt-6 text-sm text-slate-500">Loading workspaces...</p>
        ) : (
          <div className="mt-6 space-y-3">
            <AnimatePresence mode="popLayout">
              {workspaces.map((workspace) => (
                <motion.article
                  layout
                  key={workspace.id}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.2 }}
                  className="rounded-2xl border border-slate-200/75 bg-white/80 p-4 backdrop-blur"
                >
                  {activeId === workspace.id ? (
                    <div className="flex flex-col gap-3 md:flex-row">
                      <input
                        value={renameValue}
                        onChange={(event) => setRenameValue(event.target.value)}
                        className="input flex-1"
                        maxLength={255}
                      />
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => onRename(workspace.id)}
                          className="btn-primary"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setActiveId(null)
                            setRenameValue('')
                          }}
                          className="btn-ghost"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                      <div>
                        <h3 className="font-medium text-slate-900">{workspace.name}</h3>
                        <p className="text-xs text-slate-500">
                          Created {formatDate(workspace.created_at)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Link to={`/workspaces/${workspace.id}`} className="btn-primary">
                          Open
                        </Link>
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() => {
                            setMessage('')
                            setActiveId(workspace.id)
                            setRenameValue(workspace.name)
                          }}
                        >
                          Rename
                        </button>
                        <button
                          type="button"
                          className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-100"
                          onClick={() => deleteWorkspace(workspace.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  )}
                </motion.article>
              ))}
            </AnimatePresence>
            {!workspaces.length && (
              <p className="rounded-xl border border-dashed border-slate-300 px-4 py-8 text-center text-slate-500">
                No workspaces yet. Create your first workspace to get started.
              </p>
            )}
          </div>
        )}
      </motion.section>
    </div>
  )
}
