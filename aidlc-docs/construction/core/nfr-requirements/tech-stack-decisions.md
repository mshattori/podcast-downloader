# 技術スタック決定 — Unit 1: core

## 確定技術スタック

| 用途 | ライブラリ | バージョン | 選定理由 |
|---|---|---|---|
| 言語 | Python | 3.11以上 | モダンな型ヒント（`X \| Y`）、`tomllib` 内蔵、パフォーマンス改善 |
| RSSパース | `feedparser` | 6.x | Python標準的なRSS/Atom対応パーサー。`itunes:duration` 等のポッドキャスト拡張にも対応 |
| HTTPクライアント | `requests` | 2.x | ストリーミングダウンロード対応（`stream=True`）。シンプルなAPI。 |
| 設定ディレクトリ | `platformdirs` | 4.x | Windows/macOS/Linux のOS標準設定パスを返すクロスプラットフォームライブラリ |
| ログ | `logging`（標準ライブラリ） | — | 追加依存なし。`RotatingFileHandler` で自動ローテーション |
| テスト | `pytest` | 8.x | デファクトスタンダード。フィクスチャ・モックが充実 |
| テストモック | `pytest-mock` | 3.x | `MagicMock` / `patch` を pytest スタイルで使える |
| パッケージ管理 | `pyproject.toml` + `pip` | — | PEP 517/518 準拠。追加ツール不要 |

---

## 依存関係一覧（pyproject.toml）

```toml
[project]
name = "podcast-downloader"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "feedparser>=6.0",
    "requests>=2.31",
    "platformdirs>=4.0",
    "PySide6>=6.6",          # GUI ユニットで使用（core は直接依存しないが同一パッケージ）
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
]
```

---

## 採用しない技術と理由

| 技術 | 不採用理由 |
|---|---|
| `asyncio` / `aiohttp` | `threading` で十分。feedparser が同期APIのため非同期との混在が複雑 |
| `SQLite` | JSONキャッシュで十分なデータ量。スキーマ管理が不要でシンプル |
| `httpx` | `requests` で要件を満たす。追加依存を避ける |
| HTTP Range リクエスト（再開ダウンロード） | シンプルさを優先。中断時は削除して再実行 |
| リトライライブラリ（`tenacity` 等） | リトライなし方針のため不要 |

---

## 標準ライブラリ使用箇所

| 用途 | モジュール |
|---|---|
| スレッド管理 | `threading` |
| ファイルパス操作 | `pathlib.Path` |
| JSON読み書き | `json` |
| UUID生成 | `uuid` |
| 日時処理 | `datetime` |
| 正規表現（ファイル名サニタイズ） | `re` |
| URL解析（拡張子取得） | `urllib.parse` |
| ログ | `logging` |
