from app.api.schemas import AnalyzeLocationRequest, AnalyzeLocationResponse
from app.main import app
from app.modules.feng_shui.service import analyze_feng_shui_location, evaluate_lantou_heuristics, fetch_elevation_profile


def analyze_location(request: AnalyzeLocationRequest) -> AnalyzeLocationResponse:
    return AnalyzeLocationResponse.model_validate(analyze_feng_shui_location(request.lat, request.lng).__dict__)