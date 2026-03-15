import type { LocationAccuracyMode } from '../types'

type Props = {
  enabled: boolean
  accuracyMode: LocationAccuracyMode
  appUrl: string
  onToggleEnabled: () => void
  onSelectAccuracyMode: (mode: LocationAccuracyMode) => void
}

export default function LocationControl({
  enabled,
  accuracyMode,
  appUrl,
  onToggleEnabled,
  onSelectAccuracyMode,
}: Props) {
  const modes: Array<{ key: LocationAccuracyMode; label: string }> = [
    { key: 'low', label: '省電力' },
    { key: 'balanced', label: '標準' },
    { key: 'high', label: '高精度' },
  ]

  return (
    <div className="absolute top-4 left-4 z-20 w-64">
      <div className="bg-white/95 rounded-2xl shadow-md p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-gray-800">位置情報</span>
          <button
            onClick={onToggleEnabled}
            className={`relative inline-flex w-11 h-6 rounded-full transition-colors ${
              enabled ? 'bg-blue-600' : 'bg-gray-300'
            }`}
            aria-pressed={enabled}
            aria-label="位置情報のオンオフ"
            type="button"
          >
            <span
              className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                enabled ? 'translate-x-5.5' : 'translate-x-0.5'
              }`}
            />
          </button>
        </div>

        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-gray-600">精度モード</span>
          <div className="inline-flex rounded-full border border-gray-300 p-0.5 bg-gray-50">
            {modes.map((mode) => (
              <button
                key={mode.key}
                onClick={() => onSelectAccuracyMode(mode.key)}
                className={`text-[11px] font-medium px-2 py-1 rounded-full transition-colors ${
                  accuracyMode === mode.key
                    ? 'bg-emerald-500 text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
                aria-label={`位置情報精度を${mode.label}に切替`}
                type="button"
              >
                {mode.label}
              </button>
            ))}
          </div>
        </div>

        <p className="mt-2 text-[11px] leading-4 text-gray-500">
          {enabled
            ? accuracyMode === 'high'
              ? '高精度で継続取得中です。'
              : accuracyMode === 'balanced'
                ? '標準精度で継続取得中です。'
                : '省電力で継続取得中です。'
            : '位置情報の自動追従はオフです。'}
        </p>

        <div className="mt-3 border-t border-gray-200 pt-2">
          <p className="text-[11px] font-semibold text-gray-700">使い方</p>
          <p className="text-[11px] text-gray-500 leading-4 mt-1">
            1. 左上で位置情報をON
            <br />
            2. 中央の十字を見たい地点へ合わせる
            <br />
            3. 「この地点を鑑定」をタップ
          </p>
        </div>
      </div>

      <a
        href={appUrl}
        target="_blank"
        rel="noreferrer"
        className="mt-2 inline-flex items-center gap-1 bg-black/80 text-white text-xs px-3 py-1.5 rounded-full shadow hover:bg-black transition-colors"
      >
        本番Webアプリへ
      </a>
    </div>
  )
}
