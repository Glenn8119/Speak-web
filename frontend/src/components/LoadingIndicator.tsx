type LoadingType = 'chat' | 'correction'

interface LoadingIndicatorProps {
  type: LoadingType
}

const config = {
  chat: {
    label: 'Responding...',
    dotColor: 'bg-indigo-400',
    align: 'items-start' as const
  },
  correction: {
    label: 'Checking grammar...',
    dotColor: 'bg-yellow-400',
    align: 'items-end' as const
  }
}

export default function LoadingIndicator({ type }: LoadingIndicatorProps) {
  const { label, dotColor, align } = config[type]

  return (
    <div className={`flex ${align}`}>
      <div className="flex items-center gap-1.5 bg-gray-800 px-3 py-2 rounded-xl">
        <span className="text-gray-400 text-xs">{label}</span>
        <div className="flex gap-0.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className={`w-1.5 h-1.5 rounded-full ${dotColor} animate-bounce`}
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
