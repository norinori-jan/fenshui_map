import { useCallback, useRef, useState } from 'react'
import type { AnalyzeResponse } from './types'
import type { MapViewHandle } from './components/MapView'
import GsiToggle from './components/GsiToggle'
import AttributionBadge from './components/atoms/AttributionBadge'
import FabButton from './components/atoms/FabButton'
import PrimaryActionButton from './components/atoms/PrimaryActionButton'
import MapView from './components/MapView'
import LoadingToast from './components/molecules/LoadingToast'
import ResultDrawer from './components/ResultDrawer'

const INITIAL_CENTER: google.maps.LatLngLiteral = { lat: 35.6812, lng: 139.7671 }

export default function App() {
  const mapControlRef = useRef<MapViewHandle | null>(null)
  const currentCenterRef = useRef<google.maps.LatLngLiteral>(INITIAL_CENTER)

  const [gsiVisible, setGsiVisible] = useState(false)
  const [gsiOpacity, setGsiOpacity] = useState(0.5)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const handleLocate = useCallback(() => {
    if (!navigator.geolocation) {
      alert('お使いのブラウザは位置情報に対応していません。')
      return
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const loc = { lat: coords.latitude, lng: coords.longitude }
        currentCenterRef.current = loc
        mapControlRef.current?.panTo(loc)
      },
      () => alert('位置情報を取得できませんでした。\nSafari の設定 › プライバシー › 位置情報を確認してください。'),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }, [])

  const handleAnalyze = useCallback(async () => {
    const { lat, lng } = currentCenterRef.current
    setLoading(true)
    setResult(null)
    setDrawerOpen(false)

    try {
      const res = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lng }),
      })
      if (!res.ok) throw new Error(`サーバーエラー (HTTP ${res.status})`)
      const payload = (await res.json()) as AnalyzeResponse
      setResult(payload)
      setDrawerOpen(true)
    } catch (err) {
      const message = err instanceof Error ? err.message : '不明なエラー'
      setResult({ error: message })
      setDrawerOpen(true)
    } finally {
      setLoading(false)
    }
  }, [])

  return (
    <div className="relative w-screen h-dvh overflow-hidden bg-gray-200">
      <MapView
        ref={mapControlRef}
        initialCenter={INITIAL_CENTER}
        gsiVisible={gsiVisible}
        gsiOpacity={gsiOpacity}
        onCenterChange={(c) => {
          currentCenterRef.current = c
        }}
      />

      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
        <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden>
          <line x1="0" y1="16" x2="32" y2="16" stroke="#ef4444" strokeWidth="1.5" />
          <line x1="16" y1="0" x2="16" y2="32" stroke="#ef4444" strokeWidth="1.5" />
          <circle cx="16" cy="16" r="4.5" fill="none" stroke="#ef4444" strokeWidth="2" />
        </svg>
      </div>

      <GsiToggle
        active={gsiVisible}
        opacity={gsiOpacity}
        onToggle={() => setGsiVisible((v) => !v)}
        onOpacityChange={setGsiOpacity}
      />

      <AttributionBadge
        text="出典：国土地理院"
        className="z-50"
        style={{ bottom: 'calc(5rem + env(safe-area-inset-bottom, 0px))' }}
      />

      <FabButton
        onClick={handleLocate}
        className="right-4"
        style={{ bottom: 'calc(7.5rem + env(safe-area-inset-bottom, 0px))' }}
        ariaLabel="現在地に移動"
      >
        <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden>
          <circle cx="13" cy="13" r="4" fill="#2563eb" />
          <circle cx="13" cy="13" r="8.5" stroke="#2563eb" strokeWidth="1.5" />
          <line x1="13" y1="1" x2="13" y2="5.5" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="13" y1="20.5" x2="13" y2="25" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="1" y1="13" x2="5.5" y2="13" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" />
          <line x1="20.5" y1="13" x2="25" y2="13" stroke="#2563eb" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </FabButton>

      <PrimaryActionButton
        onClick={handleAnalyze}
        disabled={loading}
        style={{ bottom: 'calc(1.5rem + env(safe-area-inset-bottom, 0px))' }}
      >
        {loading ? '鑑定中…' : 'この地点を鑑定'}
      </PrimaryActionButton>

      {loading && <LoadingToast text="鑑定中..." />}

      <ResultDrawer
        open={drawerOpen}
        loading={loading}
        result={result}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  )
}
