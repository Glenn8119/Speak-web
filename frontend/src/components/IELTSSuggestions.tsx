import type { WordSuggestion } from '../types'

interface IELTSSuggestionsProps {
  suggestions: WordSuggestion[]
}

export default function IELTSSuggestions({
  suggestions
}: IELTSSuggestionsProps) {
  if (!suggestions || suggestions.length === 0) {
    return null
  }

  return (
    <section>
      <h3 className='text-sm font-medium text-gray-400 uppercase tracking-wide mb-3'>
        IELTS Vocabulary
      </h3>
      <div className='space-y-3'>
        {suggestions.map((suggestion, i) => (
          <div key={i} className='bg-gray-800 rounded-lg p-3 space-y-2'>
            <div className='flex items-center gap-2'>
              <span className='text-sm text-gray-400'>
                {suggestion.target_word}
              </span>
              <span className='text-gray-600'>→</span>
              <span className='text-sm font-medium text-indigo-300'>
                {suggestion.ielts_word}
              </span>
            </div>
            <p className='text-xs text-gray-400'>{suggestion.definition}</p>
            <div className='bg-gray-700/50 rounded p-2 space-y-1'>
              <div className='flex gap-2 text-xs'>
                <span className='text-gray-500 shrink-0'>Example:</span>
                <span className='text-gray-300 italic'>
                  {suggestion.example}
                </span>
              </div>
              <div className='flex gap-2 text-xs'>
                <span className='text-gray-500 shrink-0'>Improved:</span>
                <span className='text-green-300'>
                  {suggestion.improved_sentence}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
