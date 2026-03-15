import { useRef, type ReactNode } from 'react'

type Props = {
  open: boolean
  loading: boolean
  title: string
  onClose: () => void
  children: ReactNode
}

export default function BottomDrawer({
  open,
  loading,
  title,
  onClose,
  children,
}: Props) {
  const touchStartY = useRef<number | null>(null)
  const showBackdrop = open && !loading

  function handleTouchStart(e: React.TouchEvent<HTMLDivElement>) {
    touchStartY.current = e.touches[0].clientY
  }

  function handleTouchEnd(e: React.TouchEvent<HTMLDivElement>) {
    if (
      touchStartY.current !== null &&
      e.changedTouches[0].clientY - touchStartY.current > 80
    ) {
      onClose()
    }
    touchStartY.current = null
  }

  return (
    <>
      {showBackdrop && (
        <div
          className="absolute inset-0 z-30 bg-black/20"
          onClick={onClose}
          aria-hidden
        />
      )}

      <div
        className={`absolute bottom-0 left-0 right-0 z-40 bg-white rounded-t-3xl shadow-2xl transition-transform duration-300 ease-out max-h-[70vh] overflow-y-auto overscroll-contain ${
          open ? 'translate-y-0' : 'translate-y-full'
        }`}
        style={{ pointerEvents: loading ? 'none' : 'auto' }}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="flex justify-center pt-3 pb-1 cursor-grab">
          <div className="w-10 h-1.5 bg-gray-300 rounded-full" />
        </div>

        <div className="px-5 pb-10 pt-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-800">{title}</h2>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center text-gray-400 rounded-full hover:bg-gray-100"
              aria-label="閉じる"
            >
              ×
            </button>
          </div>

          {children}
        </div>
      </div>
    </>
  )
}
