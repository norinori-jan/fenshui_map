import { GoogleMap, useJsApiLoader } from '@react-google-maps/api'
import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'

const GSI_HILL_URL = 'https://cyberjapandata.gsi.go.jp/xyz/hillshademap/{z}/{x}/{y}.png'
const GSI_CONTOUR_URL = 'https://cyberjapandata.gsi.go.jp/xyz/contour/{z}/{x}/{y}.png'

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
  const hillLayerRef = useRef<google.maps.ImageMapType | null>(null)
  const contourLayerRef = useRef<google.maps.ImageMapType | null>(null)

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

  function createContourLayer(opacity: number): google.maps.ImageMapType {
    return new window.google.maps.ImageMapType({
      getTileUrl: (coord, zoom) =>
        GSI_CONTOUR_URL.replace('{z}', String(zoom))
          .replace('{x}', String(coord.x))
          .replace('{y}', String(coord.y)),
      tileSize: new window.google.maps.Size(256, 256),
      maxZoom: 18,
      minZoom: 5,
      opacity,
      name: 'GSI等高線',
    })
  }

  function removeOverlayByLayer(
    overlays: google.maps.MVCArray<google.maps.MapType | null>,
    layer: google.maps.ImageMapType | null,
  ) {
    if (!layer) return
    const idx = overlays.getArray().indexOf(layer)
    if (idx !== -1) overlays.removeAt(idx)
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
    const hill = hillLayerRef.current
    const contour = contourLayerRef.current
    if (!map || !hill || !contour) return

    const overlays = map.overlayMapTypes
    const hillIdx = overlays.getArray().indexOf(hill)
    const contourIdx = overlays.getArray().indexOf(contour)

    if (gsiVisible) {
      if (hillIdx === -1) overlays.push(hill)
      if (contourIdx === -1) overlays.push(contour)
    } else {
      if (hillIdx !== -1) overlays.removeAt(hillIdx)
      const nextContourIdx = overlays.getArray().indexOf(contour)
      if (nextContourIdx !== -1) overlays.removeAt(nextContourIdx)
    }
  }, [gsiVisible])

  useEffect(() => {
    const map = googleMapRef.current
    const currentHill = hillLayerRef.current
    const currentContour = contourLayerRef.current
    if (!map || !currentHill || !currentContour) return

    const overlays = map.overlayMapTypes
    const nextHill = createGsiLayer(gsiOpacity)
    const nextContour = createContourLayer(Math.min(1, gsiOpacity + 0.2))

    const hillIdx = overlays.getArray().indexOf(currentHill)
    const contourIdx = overlays.getArray().indexOf(currentContour)

    hillLayerRef.current = nextHill
    contourLayerRef.current = nextContour

    if (hillIdx !== -1) overlays.setAt(hillIdx, nextHill)
    if (contourIdx !== -1) overlays.setAt(contourIdx, nextContour)

    if (gsiVisible) {
      removeOverlayByLayer(overlays, currentHill)
      removeOverlayByLayer(overlays, currentContour)
      overlays.push(nextHill)
      overlays.push(nextContour)
    }
  }, [gsiOpacity])

  function handleMapLoad(map: google.maps.Map): void {
    googleMapRef.current = map
    hillLayerRef.current = createGsiLayer(gsiOpacity)
    contourLayerRef.current = createContourLayer(Math.min(1, gsiOpacity + 0.2))
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
