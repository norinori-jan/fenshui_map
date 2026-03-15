import { useCallback, useEffect, useRef, useState } from 'react'
import type { AnalyzeResponse, LocationAccuracyMode } from './types'
import type { MapViewHandle } from './components/MapView'
import GsiToggle from './components/GsiToggle'
import LocationControl from './components/LocationControl'
import AttributionBadge from './components/atoms/AttributionBadge'
import FabButton from './components/atoms/FabButton'
import PrimaryActionButton from './components/atoms/PrimaryActionButton'
import MapView from './components/MapView'
import LoadingToast from './components/molecules/LoadingToast'
import ResultDrawer from './components/ResultDrawer'

const DEFAULT_CENTER: google.maps.LatLngLiteral = { lat: 35.6812, lng: 139.7671 }
const FENSHUI_APP_URL = import.meta.env.VITE_FENSHUI_APP_URL ?? 'https://fenshui-app.web.app'

type TrackingProfile = {
  position: PositionOptions
  baseFollowThresholdM: number
  minPanIntervalMs: number
  maxUsableAccuracyM: number
}

const TRACKING_PROFILE: Record<LocationAccuracyMode, TrackingProfile> = {
  high: {
    position: { enableHighAccuracy: true, timeout: 10000, maximumAge: 3000 },
    baseFollowThresholdM: 12,
    minPanIntervalMs: 1200,
    maxUsableAccuracyM: 35,
  },
  balanced: {
    position: { enableHighAccuracy: false, timeout: 10000, maximumAge: 10000 },
    baseFollowThresholdM: 25,
    minPanIntervalMs: 2200,
    maxUsableAccuracyM: 60,
  },
  low: {
    position: { enableHighAccuracy: false, timeout: 15000, maximumAge: 60000 },
    baseFollowThresholdM: 45,
    minPanIntervalMs: 3500,
    maxUsableAccuracyM: 90,
  },
}

function distanceMeters(a: google.maps.LatLngLiteral, b: google.maps.LatLngLiteral): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const earthRadiusM = 6371000
  const dLat = toRad(b.lat - a.lat)
  const dLng = toRad(b.lng - a.lng)
  const lat1 = toRad(a.lat)
  const lat2 = toRad(b.lat)

  const h =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) * Math.sin(dLng / 2)
  return 2 * earthRadiusM * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h))
}

function parseSafeNumber(v: string | null): number | null {
  if (!v) return null
  const n = Number.parseFloat(v)
  return Number.isFinite(n) ? n : null
}

function toValidLatLng(
  lat: number | null,
  lng: number | null,
): google.maps.LatLngLiteral | null {
  if (lat === null || lng === null) return null
  if (lat < -90 || lat > 90) return null
  if (lng < -180 || lng > 180) return null
  return { lat, lng }
}

function resolveInitialCenterFromUrl(): google.maps.LatLngLiteral {
  if (typeof window === 'undefined') return DEFAULT_CENTER

  const params = new URLSearchParams(window.location.search)
  const lat = parseSafeNumber(params.get('lat'))
  const lng = parseSafeNumber(params.get('lng'))
  const latLng = toValidLatLng(lat, lng)
  if (latLng) return latLng

  const location = params.get('location')
  if (location) {
    const [rawLat, rawLng] = location.split(',')
    const locLat = parseSafeNumber(rawLat ?? null)
    const locLng = parseSafeNumber(rawLng ?? null)
    const locationLatLng = toValidLatLng(locLat, locLng)
    if (locationLatLng) return locationLatLng
  }

  return DEFAULT_CENTER
}

export default function App() {
  const initialCenterRef = useRef<google.maps.LatLngLiteral>(resolveInitialCenterFromUrl())
  const mapControlRef = useRef<MapViewHandle | null>(null)
  const currentCenterRef = useRef<google.maps.LatLngLiteral>(initialCenterRef.current)
  const lastFollowPanRef = useRef<google.maps.LatLngLiteral | null>(null)
  const lastFollowPanAtRef = useRef<number>(0)
  const watchIdRef = useRef<number | null>(null)

  const [gsiVisible, setGsiVisible] = useState(false)
  const [gsiOpacity, setGsiOpacity] = useState(0.5)
  const [locationEnabled, setLocationEnabled] = useState(false)
  const [accuracyMode, setAccuracyMode] = useState<LocationAccuracyMode>('high')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!navigator.geolocation) return

    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }

    if (!locationEnabled) {
      lastFollowPanRef.current = null
      lastFollowPanAtRef.current = 0
      return
    }

    const profile = TRACKING_PROFILE[accuracyMode]
    const watchId = navigator.geolocation.watchPosition(
      ({ coords }) => {
        const loc = { lat: coords.latitude, lng: coords.longitude }
        currentCenterRef.current = loc

        const currentAccuracyM = coords.accuracy
        if (currentAccuracyM > profile.maxUsableAccuracyM) return

        const now = Date.now()
        if (now - lastFollowPanAtRef.current < profile.minPanIntervalMs) return

        const dynamicThresholdM = Math.max(
          profile.baseFollowThresholdM,
          currentAccuracyM * 0.8,
        )

        const lastPan = lastFollowPanRef.current
        if (!lastPan || distanceMeters(lastPan, loc) >= dynamicThresholdM) {
          mapControlRef.current?.panTo(loc)
          lastFollowPanRef.current = loc
          lastFollowPanAtRef.current = now
        }
      },
      () => {
        alert('位置情報を継続取得できませんでした。ブラウザの位置情報許可を確認してください。')
        setLocationEnabled(false)
      },
      profile.position,
    )

    watchIdRef.current = watchId

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current)
        watchIdRef.current = null
      }
    }
  }, [locationEnabled, accuracyMode])

  const handleLocate = useCallback(() => {
    if (!navigator.geolocation) {
      alert('お使いのブラウザは位置情報に対応していません。')
      return
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const loc = { lat: coords.latitude, lng: coords.longitude }
        currentCenterRef.current = loc
        lastFollowPanRef.current = loc
        lastFollowPanAtRef.current = Date.now()
        mapControlRef.current?.panTo(loc)
      },
      () => alert('位置情報を取得できませんでした。\nSafari の設定 › プライバシー › 位置情報を確認してください。'),
      TRACKING_PROFILE[accuracyMode].position,
    )
  }, [accuracyMode])

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
        initialCenter={initialCenterRef.current}
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

      <LocationControl
        enabled={locationEnabled}
        accuracyMode={accuracyMode}
        appUrl={FENSHUI_APP_URL}
        onToggleEnabled={() => setLocationEnabled((v) => !v)}
        onSelectAccuracyMode={setAccuracyMode}
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
        ariaLabel={locationEnabled ? '現在地に更新' : '現在地に移動'}
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
