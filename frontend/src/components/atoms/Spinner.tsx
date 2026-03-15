type Props = {
  size?: 'sm' | 'md'
  className?: string
}

export default function Spinner({ size = 'md', className = '' }: Props) {
  const sizeClass = size === 'sm' ? 'w-4 h-4 border-2' : 'w-6 h-6 border-2'
  return (
    <div
      className={`${sizeClass} border-current border-t-transparent rounded-full animate-spin shrink-0 ${className}`}
      aria-hidden
    />
  )
}
