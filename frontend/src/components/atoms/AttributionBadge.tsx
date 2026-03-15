import type { CSSProperties } from 'react'

type Props = {
  text: string
  className?: string
  style?: CSSProperties
}

export default function AttributionBadge({
  text,
  className = '',
  style,
}: Props) {
  return (
    <div
      className={`absolute right-1 z-10 text-[10px] bg-white/80 px-1.5 py-0.5 rounded pointer-events-none select-none ${className}`}
      style={style}
    >
      {text}
    </div>
  )
}
