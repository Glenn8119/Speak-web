import type { Summary } from '../types'

interface SummaryModalProps {
  summary: Summary
  onClose: () => void
}

export default function SummaryModal({ summary, onClose }: SummaryModalProps) {
  const hasCorrections = summary.corrections.length > 0

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg max-h-[80vh] overflow-y-auto mx-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <h2 className="text-lg font-semibold text-gray-100">Practice Summary</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 transition-colors text-xl leading-none"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Part 1: Corrections list */}
          <section>
            <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-3">
              Corrections
            </h3>
            {hasCorrections ? (
              <div className="space-y-3">
                {summary.corrections.map((correction, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-3 space-y-1.5">
                    <div className="flex gap-2 text-xs">
                      <span className="text-gray-500">Original:</span>
                      <span className="text-gray-300">{correction.original}</span>
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className="text-gray-500">Corrected:</span>
                      <span className="text-green-300">{correction.corrected}</span>
                    </div>
                    {correction.issues.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-0.5">
                        {correction.issues.map((issue, j) => (
                          <span key={j} className="text-xs bg-gray-700 text-yellow-300 px-2 py-0.5 rounded-full">
                            {issue}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-green-300 text-sm">
                No corrections recorded — your grammar has been great!
              </p>
            )}
          </section>

          {/* Part 2: AI-generated tips */}
          {summary.tips && (
            <section>
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-2">
                Practice Tips
              </h3>
              <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                {summary.tips}
              </p>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}
