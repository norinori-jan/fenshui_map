"""Google Sheets への鑑定履歴ロギング（非同期・失敗しても本体処理を妨げない）。

必要な環境変数:
  GOOGLE_SHEETS_ID                  -- 記録先スプレッドシートの ID
  GOOGLE_APPLICATION_CREDENTIALS_JSON -- サービスアカウント JSON を文字列で (推奨)
  GOOGLE_APPLICATION_CREDENTIALS      -- サービスアカウント JSON ファイルパス (代替)

Cloud Run / Cloud Functions では GOOGLE_APPLICATION_CREDENTIALS_JSON を
Secret Manager から注入するのが安全です。ファイルパス形式はローカル開発向け。

事前準備:
  1. Google Cloud Console でサービスアカウントを作成し、キー (JSON) をダウンロード。
  2. 対象スプレッドシートの共有設定でそのサービスアカウントのメールに「編集者」権限を付与。
  3. Google Sheets API を Cloud Console で有効化。
"""

import json
import logging
import os
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials

from app.modules.feng_shui.models import FengShuiAnalysisResult

_logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_HEADER = [
    "timestamp_utc",
    "lat",
    "lng",
    "data_source",
    "shishin_souou",
    "north_support",
    "south_open",
    "confidence",
    "grounded_advice",
]


def _build_client() -> gspread.Client:
    """環境変数からサービスアカウント認証情報を読み込む。"""
    inline_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if inline_json:
        info = json.loads(inline_json)
        creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    else:
        path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not path:
            raise RuntimeError(
                "GOOGLE_APPLICATION_CREDENTIALS_JSON または "
                "GOOGLE_APPLICATION_CREDENTIALS を設定してください。"
            )
        creds = Credentials.from_service_account_file(path, scopes=_SCOPES)
    return gspread.authorize(creds)


def append_result(result: FengShuiAnalysisResult) -> None:
    """鑑定結果を Sheets に 1 行追記する。

    GOOGLE_SHEETS_ID が未設定の場合は何もしない（Sheets ロギングはオプション）。
    通信エラーや認証失敗は警告ログを出力するだけで例外を上げない。
    """
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sheet_id:
        return

    try:
        client = _build_client()
        sheet = client.open_by_key(sheet_id).sheet1

        # 先頭行が空ならヘッダーを書き込む
        if not sheet.cell(1, 1).value:
            sheet.append_row(_HEADER, value_input_option="USER_ENTERED")

        heuristics = result.heuristics or {}
        terrain = result.terrain_profile or {}

        row = [
            datetime.now(timezone.utc).isoformat(),
            result.location["lat"],
            result.location["lng"],
            terrain.get("data_source", ""),
            str(heuristics.get("shishin_souou", "")),
            str(heuristics.get("north_support", "")),
            str(heuristics.get("south_open", "")),
            heuristics.get("confidence", ""),
            # スプレッドシートのセル上限を考慮して先頭 500 文字に制限
            result.grounded_advice[:500],
        ]
        sheet.append_row(row, value_input_option="USER_ENTERED")

    except Exception:
        # Sheets ロギングはメインのレスポンスに影響させない
        _logger.warning("Sheets へのロギングに失敗しました", exc_info=True)
