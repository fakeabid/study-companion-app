import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { motion } from 'framer-motion'
import { useAuthStore } from '../stores/authStore'

export function AuthPage() {
  const [mode, setMode] = useState('login')
  const [feedback, setFeedback] = useState('')
  const { login, register: registerUser, status } = useAuthStore()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm()

  const isLogin = mode === 'login'
  const title = isLogin ? 'Welcome back' : 'Create your notesly.ai account'
  const subtitle = isLogin
    ? 'Sign in to continue building your workspace.'
    : 'Start organizing your projects in elegant workspaces.'
  const isSubmitting = status === 'loading'

  const onSubmit = async (values) => {
    setFeedback('')
    const action = isLogin ? login : registerUser
    const result = await action(values)
    if (!result.success) {
      setFeedback(result.message)
    }
  }

  const minPasswordHelp = useMemo(
    () => (isLogin ? null : 'Password must be at least 8 characters.'),
    [isLogin],
  )

  return (
    <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-10 md:px-10">
      <div className="grid w-full gap-8 md:grid-cols-2">
        <motion.section
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass-panel hidden p-10 md:flex md:flex-col md:justify-between"
        >
          <div>
            <p className="text-sm font-medium uppercase tracking-widest text-indigo-500">
              notesly.ai
            </p>
            <h1 className="mt-4 text-4xl font-semibold text-slate-900">
              Focus better, organize faster.
            </h1>
            <p className="mt-4 text-slate-600">
              Phase 1 includes secure auth and private workspaces. Crafted with a
              clean workflow and subtle motion.
            </p>
          </div>
          <ul className="space-y-3 text-sm text-slate-600">
            <li>JWT auth with auto refresh handling</li>
            <li>Workspace create, rename, and delete</li>
            <li>Responsive dashboard with smooth transitions</li>
          </ul>
        </motion.section>

        <motion.section
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1 }}
          className="glass-panel w-full p-7 md:p-10"
        >
          <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
          <p className="mt-2 text-sm text-slate-600">{subtitle}</p>

          <form className="mt-7 space-y-4" onSubmit={handleSubmit(onSubmit)}>
            {!isLogin && (
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="space-y-1">
                  <span className="label">First name</span>
                  <input
                    className="input"
                    {...register('first_name', {
                      required: 'First name is required.',
                    })}
                    placeholder="Ada"
                  />
                  {errors.first_name && (
                    <p className="input-error">{errors.first_name.message}</p>
                  )}
                </label>
                <label className="space-y-1">
                  <span className="label">Last name</span>
                  <input
                    className="input"
                    {...register('last_name', {
                      required: 'Last name is required.',
                    })}
                    placeholder="Lovelace"
                  />
                  {errors.last_name && (
                    <p className="input-error">{errors.last_name.message}</p>
                  )}
                </label>
              </div>
            )}

            <label className="space-y-1">
              <span className="label">Email</span>
              <input
                className="input"
                type="email"
                {...register('email', {
                  required: 'Email is required.',
                })}
                placeholder="you@example.com"
              />
              {errors.email && <p className="input-error">{errors.email.message}</p>}
            </label>

            <label className="space-y-1">
              <span className="label">Password</span>
              <input
                className="input"
                type="password"
                {...register('password', {
                  required: 'Password is required.',
                  minLength: isLogin ? undefined : 8,
                })}
                placeholder="••••••••"
              />
              {errors.password && (
                <p className="input-error">
                  {isLogin
                    ? errors.password.message
                    : 'Password must be at least 8 characters.'}
                </p>
              )}
              {minPasswordHelp && !errors.password && (
                <p className="text-xs text-slate-500">{minPasswordHelp}</p>
              )}
            </label>

            {feedback && (
              <p className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {feedback}
              </p>
            )}

            <motion.button
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={isSubmitting}
              className="btn-primary mt-4 w-full disabled:cursor-not-allowed disabled:opacity-80"
            >
              {isSubmitting
                ? 'Please wait...'
                : isLogin
                  ? 'Sign in'
                  : 'Create account'}
            </motion.button>
          </form>

          <button
            type="button"
            onClick={() => {
              setFeedback('')
              setMode(isLogin ? 'register' : 'login')
            }}
            className="mt-6 text-sm font-medium text-indigo-600 transition hover:text-indigo-700"
          >
            {isLogin
              ? 'New to Notesly.ai? Create an account'
              : 'Already have an account? Sign in'}
          </button>
        </motion.section>
      </div>
    </div>
  )
}
