import { GoogleMap, useJsApiLoader } from '@react-google-maps/api'
import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'

const GSI_HILL_URL = 'https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{z}/{x}/{y}.png'

const MAP_OPTIONS: google.maps.MapOptions = {
  disableDefaultUI: true,
  gestureHandling: 'greedy',
  clickableIcons: false,
}

type Props = {
  initialCenter: google.maps.LatLngLiteral
  gsiVisible: boolean
  gsiOpacity: number
  onCenterChange: (center: google.maps.LatLngLiteral) => void
}

export type MapViewHandle = {
  panTo: (latLng: google.maps.LatLngLiteral) => void
}

const MapView = forwardRef<MapViewHandle, Props>(function MapView(
  { initialCenter, gsiVisible, gsiOpacity, onCenterChange },
  ref,
) {
  const googleMapRef = useRef<google.maps.Map | null>(null)
  const gsiLayerRef = useRef<google.maps.ImageMapType | null>(null)

  function createGsiLayer(opacity: number): google.maps.ImageMapType {
    return new window.google.maps.ImageMapType({
      getTileUrl: (coord, zoom) =>
        GSI_HILL_URL.replace('{z}', String(zoom))
          .replace('{x}', String(coord.x))
          .replace('{y}', String(coord.y)),
      tileSize: new window.google.maps.Size(256, 256),
      maxZoom: 18,
      minZoom: 5,
      opacity,
      name: 'GSI陰影起伏図',
    })
  }

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? '',
  })

  useImperativeHandle(
    ref,
    () => ({
      panTo(latLng) {
        googleMapRef.current?.panTo(latLng)
      },
    }),
    [],
  )

  useEffect(() => {
    const map = googleMapRef.current
    const layer = gsiLayerRef.current
    if (!map || !layer) return

    const overlays = map.overlayMapTypes
    const idx = overlays.getArray().indexOf(layer)

    if (gsiVisible && idx === -1) overlays.push(layer)
    else if (!gsiVisible && idx !== -1) overlays.removeAt(idx)
  }, [gsiVisible])

  useEffect(() => {
    const map = googleMapRef.current
    const currentLayer = gsiLayerRef.current
    if (!map || !currentLayer) return

    const overlays = map.overlayMapTypes
    const idx = overlays.getArray().indexOf(currentLayer)
    const nextLayer = createGsiLayer(gsiOpacity)
    gsiLayerRef.current = nextLayer

    if (idx !== -1) overlays.setAt(idx, nextLayer)
  }, [gsiOpacity])

  function handleMapLoad(map: google.maps.Map): void {
    googleMapRef.current = map
    gsiLayerRef.current = createGsiLayer(gsiOpacity)
  }

  function handleIdle(): void {
    const c = googleMapRef.current?.getCenter()
    if (c) onCenterChange({ lat: c.lat(), lng: c.lng() })
  }

  if (loadError) {
    return (
      <div className="w-full h-full bg-red-50 flex items-center justify-center text-red-600 text-base p-8 text-center">
        地図の読み込みに失敗しました。
        <br />
        VITE_GOOGLE_MAPS_API_KEY を確認してください。
      </div>
    )
  }

  if (!isLoaded) {
    return (
      <div className="w-full h-full bg-gray-100 flex items-center justify-center text-gray-500 text-base">
        地図を読み込み中...
      </div>
    )
  }

  return (
    <GoogleMap
      mapContainerStyle={{ width: '100%', height: '100%' }}
      center={initialCenter}
      zoom={17}
      options={MAP_OPTIONS}
      onLoad={handleMapLoad}
      onIdle={handleIdle}
    />
  )
})

export default MapView
