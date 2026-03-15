from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.api.schemas import AnalyzeLocationRequest, AnalyzeLocationResponse
from app.modules.feng_shui.service import analyze_feng_shui_location
from app.sheets import append_result


app = FastAPI(title="Feng Shui Location Analyzer")


@app.post("/analyze", response_model=AnalyzeLocationResponse)
def analyze_location(
    request: AnalyzeLocationRequest,
    background_tasks: BackgroundTasks,
) -> AnalyzeLocationResponse:
    try:
        analysis = analyze_feng_shui_location(request.lat, request.lng)
        # Sheets ロギングはレスポンス返却後にバックグラウンドで実行（本体処理を倒さない）
        background_tasks.add_task(append_result, analysis)
        return AnalyzeLocationResponse.model_validate(analysis.__dict__)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc