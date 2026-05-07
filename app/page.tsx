'use client'
// 'use client' is required because this page uses:
//   - useState (to store question, result, loading state)
//   - event handlers (form submit, input change)
// Without 'use client', Next.js treats it as a Server Component
// which cannot use hooks or browser events.

import { useState } from 'react'
import Image from 'next/image'

// ------------------------------------------------------------------
// TypeScript type for the backend response
// Matches the ChatResponse schema from FastAPI
// ------------------------------------------------------------------
interface ChatResponse {
  question: string
  fine_tuned_answer: string
  actual_answer: string | null
  match_score_percentage: number | null
  calculation_explanation: string
}

// Backend URL — update this if your FastAPI runs on a different port
const BACKEND_URL = 'http://localhost:8000'

// ------------------------------------------------------------------
// Main page component
// ------------------------------------------------------------------
export default function TravelChatbot() {
  // State: what the user typed
  const [question, setQuestion] = useState('')
  const [actualAnswer, setActualAnswer] = useState('')

  // State: UI control
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imageError, setImageError] = useState(false)

  // State: result from backend
  const [result, setResult] = useState<ChatResponse | null>(null)

  // ----------------------------------------------------------------
  // handleSubmit: called when user clicks "Ask Travel Assistant"
  // ----------------------------------------------------------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault() // Prevent page reload on form submit

    if (!question.trim()) {
      setError('Please enter a travel question.')
      return
    }

    // Reset state before new request
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      // POST to FastAPI /chat endpoint
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.trim(),
          // Send null if no reference answer entered
          actual_answer: actualAnswer.trim() || null,
        }),
      })

      if (!response.ok) {
        // Try to get the error detail from FastAPI
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail ||
          `Server returned HTTP ${response.status}. Make sure the backend is running.`
        )
      }

      const data: ChatResponse = await response.json()
      setResult(data)

    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError(
          'Could not connect to the backend. ' +
          'Make sure FastAPI is running at localhost:8000 (see instructions below).'
        )
      }
    } finally {
      setLoading(false)
    }
  }

  // ----------------------------------------------------------------
  // Score colour helper
  // Returns a Tailwind colour class based on the score value
  // ----------------------------------------------------------------
  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-green-600'
    if (score >= 50) return 'text-yellow-600'
    return 'text-red-500'
  }

  const getBarColor = (score: number) => {
    if (score >= 75) return 'bg-green-500'
    if (score >= 50) return 'bg-yellow-400'
    return 'bg-red-400'
  }

  // ----------------------------------------------------------------
  // UI
  // ----------------------------------------------------------------
  return (
    <main className="min-h-screen" style={{ background: 'linear-gradient(to bottom, #eff6ff, #ffffff)' }}>

      {/* ---- Header ---- */}
      <header style={{ background: '#2563eb' }} className="text-white py-6 px-4 shadow-md">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold">AI Travel Assistant Chatbot</h1>
          <p style={{ color: '#bfdbfe' }} className="mt-1 text-sm">
            Powered by fine-tuned LLaMA 3.1-8B-Instruct + LoRA adapter
          </p>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">

        {/* ---- Training Proof Section ---- */}
        <section className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold mb-1" style={{ color: '#1e293b' }}>
            Training Proof
          </h2>
          <p className="text-sm mb-4" style={{ color: '#64748b' }}>
            Loss curve from fine-tuning on the travel Q&amp;A dataset.
            Loss going down = model learned travel knowledge.
          </p>

          {/* training_loss.png lives in public/ and is served at /training_loss.png */}
          <div className="relative w-full rounded-lg overflow-hidden border" style={{ height: '280px', background: '#f8fafc' }}>
            {imageError ? (
              <div className="flex flex-col items-center justify-center h-full gap-2" style={{ color: '#94a3b8' }}>
                <p className="text-sm font-medium">training_loss.png not found</p>
                <p className="text-xs text-center px-4">
                  Copy your training loss image from Google Colab to the{' '}
                  <code style={{ background: '#e2e8f0', padding: '1px 4px', borderRadius: '3px' }}>public/</code>{' '}
                  folder and name it <code style={{ background: '#e2e8f0', padding: '1px 4px', borderRadius: '3px' }}>training_loss.png</code>
                </p>
              </div>
            ) : (
              <Image
                src="/training_loss.png"
                alt="Training loss curve showing the model learning over steps"
                fill
                style={{ objectFit: 'contain' }}
                priority
                onError={() => setImageError(true)}
              />
            )}
          </div>
          <p className="text-xs mt-2" style={{ color: '#94a3b8' }}>
            Lower loss = better learning. The red dashed line shows the smoothed trend.
          </p>
        </section>

        {/* ---- Chat Form ---- */}
        <section className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4" style={{ color: '#1e293b' }}>
            Ask a Travel Question
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Question textarea */}
            <div>
              <label
                htmlFor="question"
                className="block text-sm font-medium mb-1"
                style={{ color: '#374151' }}
              >
                Your Travel Question <span style={{ color: '#ef4444' }}>*</span>
              </label>
              <textarea
                id="question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. Suggest a 3-day itinerary for Paris for a first-time traveler."
                rows={3}
                disabled={loading}
                className="w-full border rounded-lg p-3 text-sm resize-none focus:outline-none"
                style={{
                  borderColor: '#d1d5db',
                  color: '#111827',
                  opacity: loading ? 0.6 : 1,
                }}
              />
            </div>

            {/* Optional reference answer textarea */}
            <div>
              <label
                htmlFor="actualAnswer"
                className="block text-sm font-medium mb-1"
                style={{ color: '#374151' }}
              >
                Reference / Actual Answer{' '}
                <span className="font-normal text-xs" style={{ color: '#9ca3af' }}>
                  (optional — paste a known correct answer to calculate a match score)
                </span>
              </label>
              <textarea
                id="actualAnswer"
                value={actualAnswer}
                onChange={(e) => setActualAnswer(e.target.value)}
                placeholder="Paste a known correct answer here to compare with the model's response..."
                rows={3}
                disabled={loading}
                className="w-full border rounded-lg p-3 text-sm resize-none focus:outline-none"
                style={{
                  borderColor: '#d1d5db',
                  color: '#111827',
                  opacity: loading ? 0.6 : 1,
                }}
              />
            </div>

            {/* Error message */}
            {error && (
              <div
                className="rounded-lg p-3 text-sm"
                style={{ background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626' }}
              >
                {error}
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              style={{
                background: loading ? '#93c5fd' : '#2563eb',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading
                ? 'Generating answer... this may take 30-60 seconds'
                : 'Ask Travel Assistant'}
            </button>

            {/* Loading hint */}
            {loading && (
              <p className="text-xs text-center" style={{ color: '#6b7280' }}>
                The model is generating a response. LLM inference can take up to a minute on CPU.
              </p>
            )}
          </form>
        </section>

        {/* ---- Results Section ---- */}
        {result && (
          <section className="bg-white rounded-xl shadow-md p-6 space-y-6">
            <h2 className="text-xl font-semibold" style={{ color: '#1e293b' }}>Results</h2>

            {/* Your question */}
            <div>
              <h3
                className="text-xs font-semibold uppercase tracking-wider mb-2"
                style={{ color: '#6b7280' }}
              >
                Your Question
              </h3>
              <p
                className="rounded-lg p-3 text-sm"
                style={{ background: '#f8fafc', color: '#1e293b' }}
              >
                {result.question}
              </p>
            </div>

            {/* Fine-tuned model answer */}
            <div>
              <h3
                className="text-xs font-semibold uppercase tracking-wider mb-2"
                style={{ color: '#2563eb' }}
              >
                Fine-Tuned Model Answer (LLaMA 3.1 + LoRA)
              </h3>
              <div
                className="rounded-lg p-4 text-sm leading-relaxed whitespace-pre-wrap"
                style={{
                  background: '#eff6ff',
                  border: '1px solid #bfdbfe',
                  color: '#1e293b',
                }}
              >
                {result.fine_tuned_answer}
              </div>
            </div>

            {/* Reference answer (only shown if it was provided) */}
            {result.actual_answer && (
              <div>
                <h3
                  className="text-xs font-semibold uppercase tracking-wider mb-2"
                  style={{ color: '#16a34a' }}
                >
                  Reference / Actual Answer
                </h3>
                <div
                  className="rounded-lg p-4 text-sm leading-relaxed whitespace-pre-wrap"
                  style={{
                    background: '#f0fdf4',
                    border: '1px solid #bbf7d0',
                    color: '#1e293b',
                  }}
                >
                  {result.actual_answer}
                </div>
              </div>
            )}

            {/* Match score */}
            <div>
              <h3
                className="text-xs font-semibold uppercase tracking-wider mb-3"
                style={{ color: '#7c3aed' }}
              >
                Match Score
              </h3>

              {result.match_score_percentage !== null ? (
                <div className="space-y-2">
                  {/* Score number */}
                  <div className="flex items-baseline gap-2">
                    <span
                      className={`text-4xl font-bold ${getScoreColor(result.match_score_percentage)}`}
                    >
                      {result.match_score_percentage}%
                    </span>
                    <span className="text-sm" style={{ color: '#6b7280' }}>
                      semantic similarity
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div
                    className="w-full rounded-full"
                    style={{ height: '12px', background: '#e5e7eb' }}
                  >
                    <div
                      className={`rounded-full transition-all ${getBarColor(result.match_score_percentage)}`}
                      style={{
                        height: '12px',
                        width: `${Math.min(result.match_score_percentage, 100)}%`,
                      }}
                    />
                  </div>

                  {/* Scale labels */}
                  <div
                    className="flex justify-between text-xs"
                    style={{ color: '#9ca3af' }}
                  >
                    <span>0% (no match)</span>
                    <span>50% (partial)</span>
                    <span>100% (exact)</span>
                  </div>

                  {/* Score interpretation */}
                  <p className="text-xs mt-1" style={{ color: '#6b7280' }}>
                    {result.match_score_percentage >= 75
                      ? 'High match — the model answer is semantically close to the reference answer.'
                      : result.match_score_percentage >= 50
                      ? 'Moderate match — the model captured the main ideas but some details differ.'
                      : 'Low match — the model answer differs significantly from the reference answer.'}
                  </p>
                </div>
              ) : (
                <div
                  className="rounded-lg p-3 text-sm"
                  style={{ background: '#f8fafc', color: '#6b7280' }}
                >
                  No score calculated — enter a reference answer in the form above to see the match percentage.
                </div>
              )}
            </div>

            {/* Calculation explanation */}
            <div>
              <h3
                className="text-xs font-semibold uppercase tracking-wider mb-2"
                style={{ color: '#6b7280' }}
              >
                How the Score is Calculated
              </h3>
              <p
                className="rounded-lg p-3 text-sm"
                style={{ background: '#f8fafc', color: '#374151' }}
              >
                {result.calculation_explanation}
              </p>
            </div>
          </section>
        )}

        {/* ---- Run instructions ---- */}
        <section className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-xl font-semibold mb-3" style={{ color: '#1e293b' }}>
            How to Run This Project Locally
          </h2>
          <ol className="space-y-3 text-sm" style={{ color: '#374151' }}>
            <li>
              <strong>1. Start the Python backend</strong>
              <div
                className="mt-1 rounded p-3 font-mono text-xs"
                style={{ background: '#1e293b', color: '#e2e8f0' }}
              >
                cd backend<br />
                pip install -r requirements.txt<br />
                uvicorn main:app --reload --port 8000
              </div>
              <p className="text-xs mt-1" style={{ color: '#9ca3af' }}>
                Wait 2-4 min for the model to load. You will see &quot;Backend is ready!&quot; in the terminal.
              </p>
            </li>
            <li>
              <strong>2. Start the Next.js frontend</strong>
              <div
                className="mt-1 rounded p-3 font-mono text-xs"
                style={{ background: '#1e293b', color: '#e2e8f0' }}
              >
                npm run dev
              </div>
              <p className="text-xs mt-1" style={{ color: '#9ca3af' }}>
                Opens at http://localhost:3000
              </p>
            </li>
            <li>
              <strong>3. Set your HF token</strong>
              <div
                className="mt-1 rounded p-3 font-mono text-xs"
                style={{ background: '#1e293b', color: '#e2e8f0' }}
              >
                {/* Windows */}set HF_TOKEN=hf_your_token_here<br />
                {/* Then restart the backend */}uvicorn main:app --reload --port 8000
              </div>
            </li>
          </ol>
        </section>

        {/* ---- Footer ---- */}
        <footer className="text-center text-xs pb-8" style={{ color: '#9ca3af' }}>
          AI Travel Assistant — LLaMA 3.1-8B-Instruct + LoRA Fine-Tuning
        </footer>

      </div>
    </main>
  )
}
