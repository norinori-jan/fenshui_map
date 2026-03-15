import Spinner from '../atoms/Spinner'

type Props = {
  text?: string
}

export default function LoadingToast({ text = '処理中...' }: Props) {
  return (
    <div className="absolute top-16 left-1/2 -translate-x-1/2 z-30 pointer-events-none">
      <div className="flex items-center gap-2 bg-white/95 text-amber-700 px-3 py-2 rounded-full shadow-lg text-sm">
        <Spinner size="sm" />
        <span>{text}</span>
      </div>
    </div>
  )
}
