import type { CSSProperties, MouseEventHandler, ReactNode } from 'react'

type Props = {
  onClick?: MouseEventHandler<HTMLButtonElement>
  disabled?: boolean
  children: ReactNode
  className?: string
  style?: CSSProperties
}

export default function PrimaryActionButton({
  onClick,
  disabled,
  children,
  className = '',
  style,
}: Props) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`absolute left-1/2 -translate-x-1/2 z-20 h-14 px-10 bg-amber-700 disabled:bg-amber-400 text-white text-lg font-bold rounded-2xl shadow-xl active:scale-95 transition-transform whitespace-nowrap ${className}`}
      style={style}
    >
      {children}
    </button>
  )
}
