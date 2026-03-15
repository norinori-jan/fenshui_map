# fenshui_map

共有コアを前提にした風水鑑定バックエンドの初期構成です。

## モジュール構成

| 項目 | 易モジュール | 風水モジュール | 共有コア (Registry A) |
| --- | --- | --- | --- |
| 主な役割 | 卦を立てる・解釈 | 地形・方位の分析 | 五行・方位・暦の計算 |
| 依存先 | 共有コアを参照 | 共有コアを参照 | なし |
| データ例 | 本卦・変卦のデータ | 標高・龍脈のデータ | 干支・八卦の定義値 |

## 現在の配置

- app/core/registry_a.py
	- 共有コア。方位、五行、地支の定義を保持します。
- app/modules/iching/service.py
	- 易モジュールの雛形。共有コアを参照します。
- app/modules/feng_shui/service.py
	- Google Maps grounding と Elevation API を使う風水分析本体です。
- app/main.py
	- FastAPI の入口です。

## 今後の共有方針

- norinori-jan/fortune の八卦・六十四卦データは、将来的に易モジュールへ移し、共有コアの方位・五行定義を参照させます。
- norinori-jan/fengshui-app の地形・方位ロジックは、共有コアの方位定義を参照する形で寄せます。
- 本リポジトリでは、まず Registry A を独立させ、両モジュールがそこだけを共通依存にする構造を先に固定します。

## Final Migration Plan

### 1. fortune-core の独立リポジトリ化

fortune-core ディレクトリには、独立リポジトリ化用のスクリプトを配置しています。

```bash
cd /workspaces/fenshui_map/fortune-core
chmod +x scripts/init_and_push_fortune_core.sh
./scripts/init_and_push_fortune_core.sh /workspaces/fortune-core-repo

cd /workspaces/fortune-core-repo
git push -u origin main
```

pyproject.toml では以下が設定済みです。

- `include-package-data = true`
- `[tool.setuptools.package-data]`
- `fortune_core = ["data/*.json"]`

これにより `src/fortune_core/data/hexagrams.json` は sdist と wheel の両方に同梱されます。

### 2. 各アプリの requirements.txt 差し替え

norinori-jan/fortune:

```text
fortune-core @ git+https://github.com/norinori-jan/fortune-core.git@main
```

norinori-jan/fengshui-app:

```text
fortune-core @ git+https://github.com/norinori-jan/fortune-core.git@main
```

### 3. fortune 側の安全なリファクタリング手順

1. `backend/hexagrams.py` を即削除せず、まず利用箇所を検索する。
2. `from hexagrams import ...` を `from fortune_core.hexagrams import ...` に置き換える。
3. `TRIGRAMS` と `HEXAGRAMS` の直接参照は、`load_trigrams()` と `load_hexagrams()` に置き換える。
4. 変爻計算や `get_line_names()` の呼び出しは、fortune_core 側 API に寄せる。
5. backend テストを fortune_core 参照へ更新してから、旧 `backend/hexagrams.py` を削除する。

VS Code の検索置換候補:

```text
検索: from hexagrams import (.+)
置換: from fortune_core.hexagrams import $1
```

```text
検索: import hexagrams
置換: import fortune_core.hexagrams as hexagrams
```

### 4. fenshui_map 側の旧互換層 削除忘備録

`app/modules/feng_shui/service.py` が `fortune_core` を直接参照するように書き換え終わった後で、以下を削除候補にする。

```bash
cd /workspaces/fenshui_map
rm app/core/registry_a.py
rm app/feng_shui_service.py
```

fortune 側で旧六十四卦定義を撤去する場合:

```bash
cd /workspaces/fortune
rm backend/hexagrams.py
```

fengshui-app 側で旧 Registry A 定義を撤去する場合は、対象ファイルを検索してから削除する。

```bash
cd /workspaces/fengshui-app
rg -l "registry_a|DIRECTIONS =|FIVE_ELEMENTS =|DirectionProfile|get_direction_profile"
rm path/to/registry_a.py
```

## Firebase + Cloud Run デプロイ準備（機密情報をコードに直書きしない）

本リポジトリは以下の方針でデプロイします。

- フロントエンド: Firebase Hosting
- バックエンド: Cloud Run（FastAPI）
- 秘密情報: Secret Manager（Git 管理しない）

### 1) 事前に設定する GitHub Secrets

GitHub リポジトリの `Settings > Secrets and variables > Actions` で、次を設定します。

- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT_EMAIL`
- `VITE_GOOGLE_MAPS_API_KEY` （ブラウザ向け。必ずリファラ制限を有効化）

補足: `VITE_` で始まる値はビルド後にクライアントへ配布されるため、完全秘匿は不可能です。必ず API 制限・HTTP リファラ制限で保護してください。

### 2) Secret Manager へサーバー機密を登録

ローカルで次を実行します。

```bash
export GCP_PROJECT_ID="your-project-id"
export GEMINI_API_KEY="***"
export GOOGLE_MAPS_API_KEY_SERVER="***"
export GOOGLE_SHEETS_ID="***"
export GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'

bash scripts/set_gcp_secrets.sh
```

### 3) Cloud Run へデプロイ

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="asia-northeast1"
export CLOUD_RUN_SERVICE="fengshui-api"

bash scripts/deploy_cloudrun.sh
```

### 4) Firebase Hosting へデプロイ

`firebase.json` は `frontend/dist` を配信し、`/analyze` を Cloud Run にリライトします。

初回のみ:

```bash
firebase login
firebase use --add
```

以降:

```bash
cd frontend && npm ci && npm run build && cd ..
firebase deploy --only hosting
```

### 5) 自動デプロイ（main push）

`.github/workflows/deploy-firebase-cloudrun.yml` により、`main` へ push すると以下が自動実行されます。

1. フロントの `tsc --noEmit` 厳格型チェック（失敗時は中断）
2. フロントビルド
3. GitHub Secrets の値を Secret Manager に同期
4. Cloud Run デプロイ
5. Firebase Hosting デプロイ
6. Cloud Run / Hosting の URL へ curl ヘルスチェック（HTTP 200 必須）

これにより、VS Code 上の「コミット & プッシュ」だけで本番更新できます。

必要な GitHub Secrets:

- `GCP_PROJECT_ID`
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT_EMAIL`
- `VITE_GOOGLE_MAPS_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_MAPS_API_KEY_SERVER`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`