import type { ReactNode } from 'react'

// The agent's replies follow a fixed structure (numbered sections, occasional
// bullet lists, **bold** emphasis) but arrive as plain text -- no markdown
// library in this project, so this renders just enough of it to read cleanly
// instead of dumping everything into one unbroken <pre> block.
const LINK = /(\[[^\]]+\]\(https?:\/\/[^)\s]+\)|https?:\/\/[^\s)]+|\*\*[^*]+\*\*)/g

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  return text
    .split(LINK)
    .filter((part) => part !== '')
    .map((part, i) => {
      const key = `${keyPrefix}-${i}`

      const mdLink = part.match(/^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/)
      if (mdLink) {
        return (
          <a key={key} href={mdLink[2]} target="_blank" rel="noreferrer" className="underline break-words" style={{ color: 'var(--accent)' }}>
            {mdLink[1]}
          </a>
        )
      }

      if (/^https?:\/\//.test(part)) {
        // Split off trailing sentence punctuation (e.g. "...page." or "source,")
        // so it isn't swallowed into the link itself.
        const [, url, trailing] = part.match(/^(https?:\/\/.*?)([.,;:!?]*)$/) ?? [null, part, '']
        return (
          <span key={key}>
            <a href={url} target="_blank" rel="noreferrer" className="underline break-words" style={{ color: 'var(--accent)' }}>
              {url}
            </a>
            {trailing}
          </span>
        )
      }

      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={key}>{part.slice(2, -2)}</strong>
      }
      return <span key={key}>{part}</span>
    })
}

export function MarkdownLite({ text }: { text: string }) {
  const lines = text.split('\n')
  const blocks: ReactNode[] = []
  let i = 0
  let n = 0

  while (i < lines.length) {
    if (lines[i].trim() === '') {
      i++
      continue
    }

    if (/^\d+\.\s+/.test(lines[i])) {
      const items: string[] = []
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\.\s+/, ''))
        i++
      }
      blocks.push(
        <ol key={n} className="list-decimal pl-5 flex flex-col gap-1.5">
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item, `${n}-${idx}`)}</li>
          ))}
        </ol>,
      )
      n++
      continue
    }

    if (/^[-*]\s+/.test(lines[i])) {
      const items: string[] = []
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ''))
        i++
      }
      blocks.push(
        <ul key={n} className="list-disc pl-5 flex flex-col gap-1.5">
          {items.map((item, idx) => (
            <li key={idx}>{renderInline(item, `${n}-${idx}`)}</li>
          ))}
        </ul>,
      )
      n++
      continue
    }

    const headingMatch = lines[i].match(/^#{1,4}\s+(.*)/)
    if (headingMatch) {
      blocks.push(
        <p key={n} className="font-semibold text-[var(--text-h)]">
          {renderInline(headingMatch[1], `${n}`)}
        </p>,
      )
      n++
      i++
      continue
    }

    const paraLines: string[] = []
    while (i < lines.length && lines[i].trim() !== '' && !/^\d+\.\s+|^[-*]\s+|^#{1,4}\s+/.test(lines[i])) {
      paraLines.push(lines[i])
      i++
    }
    blocks.push(<p key={n}>{renderInline(paraLines.join(' '), `${n}`)}</p>)
    n++
  }

  return <div className="flex flex-col gap-2.5">{blocks}</div>
}
