import type { CSSProperties, MouseEventHandler, ReactNode } from 'react'

type Props = {
  onClick?: MouseEventHandler<HTMLButtonElement>
  children: ReactNode
  ariaLabel: string
  className?: string
  style?: CSSProperties
}

export default function FabButton({
  onClick,
  children,
  ariaLabel,
  className = '',
  style,
}: Props) {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel}
      className={`absolute z-20 w-14 h-14 bg-white rounded-full shadow-lg flex items-center justify-center active:scale-95 transition-transform ${className}`}
      style={style}
    >
      {children}
    </button>
  )
}
