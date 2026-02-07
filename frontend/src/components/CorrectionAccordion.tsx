import { useState } from 'react'
import type { Correction } from '../types'

interface CorrectionAccordionProps {
  correction: Correction
}

export default function CorrectionAccordion({ correction }: CorrectionAccordionProps) {
  const [isOpen, setIsOpen] = useState(false)
  const hasIssues = correction.issues.length > 0
  const isUnavailable = correction.explanation?.includes('unavailable')

  // Determine the button label based on state
  const getButtonLabel = () => {
    if (isUnavailable) return 'Grammar check unavailable'
    if (hasIssues) return `${correction.issues.length} correction${correction.issues.length !== 1 ? 's' : ''}`
    return 'No corrections needed'
  }

  // Determine button color based on state
  const buttonColorClass = isUnavailable
    ? 'text-gray-500 hover:text-gray-400'
    : 'text-indigo-300 hover:text-indigo-200'

  return (
    <div className="w-full max-w-sm">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full flex items-center justify-between text-xs transition-colors cursor-pointer ${buttonColorClass}`}
        aria-expanded={isOpen}
      >
        <span>{getButtonLabel()}</span>
        <span className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}>▾</span>
      </button>

      {isOpen && (
        <div className="mt-2 p-3 bg-gray-800 rounded-lg border border-gray-700 text-sm space-y-2 animate-slide-down">
          {isUnavailable ? (
            <p className="text-gray-400 text-xs">{correction.explanation}</p>
          ) : hasIssues ? (
            <>
              <div>
                <span className="text-gray-400 text-xs uppercase tracking-wide">Corrected</span>
                <p className="text-green-300 mt-0.5">{correction.corrected}</p>
              </div>

              <div>
                <span className="text-gray-400 text-xs uppercase tracking-wide">Issues</span>
                <ul className="mt-0.5 space-y-0.5">
                  {correction.issues.map((issue, i) => (
                    <li key={i} className="text-yellow-300 text-xs">• {issue}</li>
                  ))}
                </ul>
              </div>

              <div>
                <span className="text-gray-400 text-xs uppercase tracking-wide">Explanation</span>
                <p className="text-gray-300 text-xs mt-0.5">{correction.explanation}</p>
              </div>
            </>
          ) : (
            <p className="text-green-300 text-xs">{correction.explanation || 'Your grammar looks great!'}</p>
          )}
        </div>
      )}
    </div>
  )
}
