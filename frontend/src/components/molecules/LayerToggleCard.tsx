type Props = {
  active: boolean
  label: string
  value: number
  min: number
  max: number
  step: number
  unit?: string
  onToggle: () => void
  onChange: (value: number) => void
}

export default function LayerToggleCard({
  active,
  label,
  value,
  min,
  max,
  step,
  unit = '',
  onToggle,
  onChange,
}: Props) {
  return (
    <div className="absolute top-4 right-4 z-20 w-56">
      <button
        onClick={onToggle}
        className={`flex items-center gap-2 pl-3 pr-2 rounded-full shadow-md min-h-[44px] text-sm font-medium transition-colors ${
          active ? 'bg-emerald-600 text-white' : 'bg-white text-gray-700'
        }`}
        aria-pressed={active}
        aria-label={label}
      >
        <span aria-hidden>🗾</span>
        <span>{label}</span>
        <span
          className={`relative w-9 h-5 rounded-full mx-1 transition-colors ${
            active ? 'bg-emerald-400' : 'bg-gray-300'
          }`}
        >
          <span
            className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${
              active ? 'translate-x-4' : 'translate-x-0.5'
            }`}
          />
        </span>
      </button>

      {active && (
        <div className="mt-2 bg-white/95 rounded-xl px-3 py-2 shadow-md">
          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>透過度</span>
            <span>
              {value.toFixed(2)}
              {unit}
            </span>
          </div>
          <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(e) => onChange(Number(e.target.value))}
            className="w-full h-6"
            aria-label={`${label}透過度`}
          />
        </div>
      )}
    </div>
  )
}
