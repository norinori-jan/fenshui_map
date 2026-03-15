import LayerToggleCard from './molecules/LayerToggleCard'

type Props = {
  active: boolean
  opacity: number
  onToggle: () => void
  onOpacityChange: (value: number) => void
}

/**
 * 風水マップ向け設定済みラッパー。
 * 内部は汎用 LayerToggleCard を利用し、他アプリでも流用しやすくする。
 */
export default function GsiToggle({ active, opacity, onToggle, onOpacityChange }: Props) {
  return (
    <LayerToggleCard
      active={active}
      label="地理院図"
      value={opacity}
      min={0.35}
      max={1}
      step={0.05}
      onToggle={onToggle}
      onChange={onOpacityChange}
    />
  )
}
