export type LatLng = {
  lat: number
  lng: number
}

export type LocationAccuracyMode = 'low' | 'balanced' | 'high'

export type TerrainProfile = {
  center_elevation_m: number | null
  north_avg_elevation_m: number | null
  south_avg_elevation_m: number | null
  east_avg_elevation_m: number | null
  west_avg_elevation_m: number | null
  data_source?: string
}

export type Heuristics = {
  shishin_souou?: boolean | null
  north_support?: boolean | null
  south_open?: boolean | null
  east_guard?: boolean | null
  west_guard?: boolean | null
  road_collision_risk?: boolean | null
  confidence?: string
}

export type AnalyzeSuccessResponse = {
  grounded_advice?: string
  heuristics?: Heuristics
  terrain_profile?: TerrainProfile | null
}

export type AnalyzeErrorResponse = {
  error: string
}

export type AnalyzeResponse = AnalyzeSuccessResponse | AnalyzeErrorResponse

export function isAnalyzeError(v: AnalyzeResponse | null): v is AnalyzeErrorResponse {
  return !!v && typeof (v as AnalyzeErrorResponse).error === 'string'
}
