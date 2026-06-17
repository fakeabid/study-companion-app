import { motion } from 'framer-motion'

const bubbles = [
  { size: 'h-60 w-60', position: '-top-16 -left-10', delay: 0 },
  { size: 'h-72 w-72', position: 'top-1/3 -right-16', delay: 1.2 },
  { size: 'h-48 w-48', position: 'bottom-10 left-1/4', delay: 0.6 },
]

export function AnimatedBackground() {
  return (
    <div className="pointer-events-none fixed inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-indigo-50 via-white to-violet-50" />
      {bubbles.map((bubble, index) => (
        <motion.div
          // Stable data set, safe to key by index.
          key={index}
          className={`absolute ${bubble.size} ${bubble.position} rounded-full bg-gradient-to-tr from-indigo-300/30 to-fuchsia-300/20 blur-3xl`}
          initial={{ opacity: 0.35, y: 0 }}
          animate={{ opacity: [0.3, 0.55, 0.3], y: [0, -20, 0], x: [0, 15, 0] }}
          transition={{
            duration: 10,
            ease: 'easeInOut',
            repeat: Number.POSITIVE_INFINITY,
            delay: bubble.delay,
          }}
        />
      ))}
    </div>
  )
}
