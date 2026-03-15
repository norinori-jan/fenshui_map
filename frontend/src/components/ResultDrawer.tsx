import Spinner from './atoms/Spinner'
import BottomDrawer from './organisms/BottomDrawer'
import type { AnalyzeResponse, Heuristics, TerrainProfile } from '../types'
import { isAnalyzeError } from '../types'

type Props = {
  open: boolean
  loading: boolean
  result: AnalyzeResponse | null
  onClose: () => void
}

export default function ResultDrawer({ open, loading, result, onClose }: Props) {
  return (
    <BottomDrawer
      open={open}
      loading={loading}
      title="風水鑑定結果"
      onClose={onClose}
    >
      {loading && <LoadingState />}
      {!loading && isAnalyzeError(result) && <ErrorState message={result.error} />}
      {!loading && result && !isAnalyzeError(result) && <AnalysisResult result={result} />}
    </BottomDrawer>
  )
}

function LoadingState() {
  return (
    <div className="flex items-center gap-3 text-amber-700 py-4">
      <Spinner />
      <span className="text-base">Gemini が鑑定中...</span>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-red-50 rounded-2xl p-4">
      <p className="text-red-700 text-base">エラー: {message}</p>
    </div>
  )
}

function AnalysisResult({ result }: { result: Exclude<AnalyzeResponse, { error: string }> }) {
  return (
    <div className="space-y-4">
      <AdviceSection advice={result.grounded_advice} />
      <HeuristicsSection heuristics={result.heuristics} />
      <TerrainSection profile={result.terrain_profile ?? null} />
      <AttributionFooter dataSource={result.terrain_profile?.data_source} />
    </div>
  )
}

function AdviceSection({ advice }: { advice?: string }) {
  if (!advice) return null
  return (
    <div className="bg-amber-50 rounded-2xl p-4">
      <h3 className="text-sm font-semibold text-amber-800 mb-2">鑑定コメント</h3>
      <p className="text-base text-gray-700 whitespace-pre-line leading-relaxed">
        {advice}
      </p>
    </div>
  )
}

function HeuristicsSection({ heuristics }: { heuristics?: Heuristics }) {
  if (!heuristics) return null
  const {
    shishin_souou,
    north_support,
    south_open,
    east_guard,
    west_guard,
    road_collision_risk,
    confidence,
  } = heuristics

  return (
    <div className="bg-emerald-50 rounded-2xl p-4">
      <h3 className="text-sm font-semibold text-emerald-800 mb-3">四神相応チェック</h3>
      <div className="grid grid-cols-2 gap-y-2 text-base">
        <CheckRow label="四神相応（総合）" value={shishin_souou ?? null} />
        <CheckRow label="玄武（北に山）" value={north_support ?? null} />
        <CheckRow label="朱雀（南が開ける）" value={south_open ?? null} />
        <CheckRow label="青龍（東に護り）" value={east_guard ?? null} />
        <CheckRow label="白虎（西に護り）" value={west_guard ?? null} />
        {road_collision_risk === true && (
          <div className="col-span-2 mt-1 text-sm text-orange-700 bg-orange-50 rounded-lg px-3 py-1.5">
            ⚠️ 路衝リスクあり
          </div>
        )}
      </div>
      <p className="text-xs text-gray-400 mt-3">信頼度: {confidence ?? '不明'}</p>
    </div>
  )
}

function TerrainSection({ profile }: { profile: TerrainProfile | null }) {
  if (!profile) return null
  return (
    <div className="bg-blue-50 rounded-2xl p-4">
      <h3 className="text-sm font-semibold text-blue-800 mb-3">標高プロファイル</h3>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-base">
        <Pair label="中心" value={fmt(profile.center_elevation_m)} />
        <Pair label="北側平均" value={fmt(profile.north_avg_elevation_m)} />
        <Pair label="南側平均" value={fmt(profile.south_avg_elevation_m)} />
        <Pair label="東側平均" value={fmt(profile.east_avg_elevation_m)} />
        <Pair label="西側平均" value={fmt(profile.west_avg_elevation_m)} />
      </dl>
    </div>
  )
}

function AttributionFooter({ dataSource }: { dataSource?: string }) {
  const isGsi = dataSource?.includes('gsi')
  return (
    <p className="text-xs text-gray-400 text-center pt-2">
      {isGsi ? '標高データ: 国土地理院 / CC-BY 4.0' : `データソース: ${dataSource ?? '不明'}`}
    </p>
  )
}

function CheckRow({ label, value }: { label: string; value: boolean | null }) {
  const icon = value === true ? '✅' : value === false ? '❌' : '—'
  return (
    <>
      <span className="text-gray-700">{label}</span>
      <span>{icon}</span>
    </>
  )
}

function Pair({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-gray-500">{label}</dt>
      <dd className="font-medium text-gray-800">{value}</dd>
    </>
  )
}

function fmt(v: number | null | undefined) {
  return v != null ? `${v.toFixed(1)} m` : '—'
}
