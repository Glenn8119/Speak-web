import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className='flex flex-col items-center justify-center min-h-screen bg-gray-950 text-white'>
      <div className='flex gap-6'>
        <a href='https://vite.dev' target='_blank'>
          <img
            src={viteLogo}
            className='h-24 p-4 cursor-pointer transition-filter duration-300 hover:drop-shadow-[0_0_2em_#646cffaa]'
            alt='Vite logo'
          />
        </a>
        <a href='https://react.dev' target='_blank'>
          <img
            src={reactLogo}
            className='h-24 p-4 cursor-pointer transition-filter duration-300 hover:drop-shadow-[0_0_2em_#61dafb]'
            alt='React logo'
          />
        </a>
      </div>
      <h1 className='text-5xl font-bold mt-6'>Vite + React</h1>
      <div className='mt-8 p-8 rounded-lg border border-gray-700 text-center'>
        <button
          className='px-4 py-2 rounded border border-gray-600 hover:border-gray-400 transition-colors cursor-pointer'
          onClick={() => setCount((count) => count + 1)}
        >
          count is {count}
        </button>
        <p className='mt-4'>
          Edit <code className='text-indigo-400'>src/App.tsx</code> and save to
          test HMR
        </p>
      </div>
      <p className='mt-6 text-gray-500'>
        Click on the Vite and React logos to learn more
      </p>
    </div>
  )
}

export default App
