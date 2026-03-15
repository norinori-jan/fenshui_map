# fortune-core

易アプリと風水アプリで共通利用する Python パッケージです。

## 標準構成

```text
fortune-core/
├── pyproject.toml
├── README.md
├── src/
│   └── fortune_core/
│       ├── __init__.py
│       ├── enums.py
│       ├── directions.py
│       ├── calendar.py
│       ├── hexagrams.py
│       └── data/
│           └── hexagrams.json
└── tests/
  ├── test_directions.py
  └── test_hexagrams.py
```

## 収録内容

- enums.py
  - 五行 Enum
  - 八卦 Enum
- directions.py
  - 方位セクター定義
  - 方位角から方位を求めるロジック
  - 方位と八卦・五行の対応
- calendar.py
  - 地支 Enum
  - 地支と方位の対応
- hexagrams.py
  - 八卦・六十四卦の dataclass
  - JSON リソースを読み込む API
  - 変爻計算

## データ管理方針

- 八卦や五行の Enum、方位計算ロジックのような振る舞いは Python コードで管理します。
- 六十四卦のように件数が多く、主に定数データとして保守するものは JSON リソースで管理します。
- 理由:
  - 差分レビューがしやすい
  - 将来 UI や他言語実装と共有しやすい
  - データ修正で Python ロジックを触らずに済む
  - コードとデータの責務を分離できる

このため、保守性の観点では六十四卦データはコード直書きより JSON リソース管理を推奨します。

## 他リポジトリからの利用例

requirements.txt:

```text
fortune-core @ git+https://github.com/norinori-jan/fortune-core.git@main
```

タグ固定の例:

```text
fortune-core @ git+https://github.com/norinori-jan/fortune-core.git@v0.1.0
```