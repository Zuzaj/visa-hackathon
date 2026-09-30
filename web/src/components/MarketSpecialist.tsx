import { Download, Maximize2, Minimize2, Sparkles, Send, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, type AgentMessage } from '../lib/api'
import { MarkdownLite } from './MarkdownLite'

const EXAMPLE_PROMPTS = [
  'What should I do with this data?',
  'What does this data mean for Lidl Poznań?',
  'What problems could this reveal?',
  "What's happening in Poznań that could explain this?",
  'Describe me briefly the market in Poznań',
]

// Floating assistant available on every tab (not just one step of the
// journey) -- it reads whichever month the director currently has selected,
// so "this data" in a question always means what's on screen.
export function MarketSpecialist({ month }: { month: number | null }) {
  const [open, setOpen] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  async function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed || loading) return
    const next = [...messages, { role: 'user' as const, content: trimmed }]
    setMessages(next)
    setInput('')
    setError(null)
    setLoading(true)
    try {
      const reply = await api.agentChat(next, month)
      setMessages([...next, { role: 'assistant' as const, content: reply }])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  function downloadTranscript() {
    const header = `Wallet Radar — AI Market Specialist conversation\n${new Date().toLocaleString()}\n`
    const body = messages
      .map((m) => `${m.role === 'user' ? 'You' : 'Market Specialist'}:\n${m.content}`)
      .join('\n\n---\n\n')
    const blob = new Blob([`${header}\n${body}\n`], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `market-specialist-${new Date().toISOString().slice(0, 10)}.txt`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      {open && (
        <div
          className={
            'fixed z-40 flex flex-col overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--panel)] ' +
            (expanded ? 'inset-6' : 'bottom-24 right-6 w-[min(560px,calc(100vw-3rem))]')
          }
          style={{
            height: expanded ? undefined : 'min(760px, calc(100vh - 8rem))',
            boxShadow: 'var(--shadow-md)',
          }}
        >
          <div
            className="flex items-center justify-between px-4 py-3 text-white"
            style={{ background: 'var(--accent)' }}
          >
            <div className="flex items-center gap-2 font-semibold text-sm">
              <Sparkles size={16} />
              AI Market Specialist
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={downloadTranscript}
                disabled={messages.length === 0}
                className="opacity-80 hover:opacity-100 disabled:opacity-30 disabled:cursor-not-allowed"
                aria-label="Download conversation"
                title="Download conversation"
              >
                <Download size={17} />
              </button>
              <button
                onClick={() => setExpanded((v) => !v)}
                className="opacity-80 hover:opacity-100"
                aria-label={expanded ? 'Collapse' : 'Expand'}
                title={expanded ? 'Collapse' : 'Expand'}
              >
                {expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
              </button>
              <button onClick={() => setOpen(false)} className="opacity-80 hover:opacity-100" aria-label="Close">
                <X size={18} />
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3">
            <div className="max-w-2xl mx-auto flex flex-col gap-3">
              {messages.length === 0 && (
                <div className="flex flex-col gap-3">
                  <p className="text-sm text-[var(--text-muted)]">
                    Ask about this month's numbers, what they mean, or what to do next. I can also look up what's
                    happening in Poznań to add context.
                  </p>
                  <div className="flex flex-col gap-2">
                    {EXAMPLE_PROMPTS.map((p) => (
                      <button
                        key={p}
                        onClick={() => send(p)}
                        className="text-left text-sm rounded-lg border border-[var(--border)] px-3 py-2 text-[var(--text)] hover:border-[var(--accent)] transition-colors"
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m, i) =>
                m.role === 'user' ? (
                  <div
                    key={i}
                    className="self-end max-w-[85%] rounded-xl px-3 py-2 text-sm whitespace-pre-wrap text-white"
                    style={{ background: 'var(--accent)' }}
                  >
                    {m.content}
                  </div>
                ) : (
                  <div key={i} className="self-start w-full rounded-xl px-3.5 py-3 text-sm leading-relaxed text-[var(--text)]" style={{ background: 'var(--bg)' }}>
                    <MarkdownLite text={m.content} />
                  </div>
                ),
              )}

              {loading && (
                <div
                  className="self-start flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm text-[var(--text-muted)]"
                  style={{ background: 'var(--bg)' }}
                >
                  <span>Thinking</span>
                  <span className="flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--accent)', animationDelay: '0ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--accent)', animationDelay: '150ms' }} />
                    <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--accent)', animationDelay: '300ms' }} />
                  </span>
                </div>
              )}

              {error && <div className="self-start text-xs text-[var(--bad)]">{error}</div>}
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              send(input)
            }}
            className="border-t border-[var(--border)] p-3"
          >
            <div className="max-w-2xl mx-auto flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask the AI market specialist…"
                className="flex-1 rounded-lg border border-[var(--border)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)]"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="flex items-center justify-center rounded-lg p-2 text-white disabled:opacity-40"
                style={{ background: 'var(--accent)' }}
                aria-label="Send"
              >
                <Send size={16} />
              </button>
            </div>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((v) => !v)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold text-white"
        style={{ background: 'var(--accent)', boxShadow: 'var(--shadow-md)' }}
      >
        <Sparkles size={16} />
        AI Market Specialist
      </button>
    </>
  )
}
