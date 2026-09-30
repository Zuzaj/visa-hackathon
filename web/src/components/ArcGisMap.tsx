interface Props {
  src: string
  title?: string
  height?: number
}

export function ArcGisMap({ src, title = 'Map', height = 600 }: Props) {
  return (
    <iframe
      src={src}
      title={title}
      width="100%"
      height={height}
      allow="local-network-access; geolocation"
      style={{ border: 0, display: 'block' }}
      className="rounded-xl overflow-hidden border border-[var(--border)]"
    />
  )
}
