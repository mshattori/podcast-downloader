# ユニット生成計画

アプリケーション設計で確定したコンポーネント構成に基づき、2ユニットに分割します。

---

## 想定ユニット構成

| ユニット | 内容 | 依存 |
|---|---|---|
| **Unit 1: core** | models / rss_parser / duration_parser / downloader / settings_manager | なし |
| **Unit 2: gui** | main_window / feed_panel / episode_list / download_panel / settings_dialog / main.py | Unit 1 |

---

## 質問 1 — 開発順序

Unit 1（core）を先に完成させてからUnit 2（gui）へ進みますか？

A) はい — Unit 1を完成させてからUnit 2へ（コアロジックを固めてからUI実装）

B) いいえ — 両ユニットを並行して進める（スタブを使いながら同時開発）

C) Other (以下に記述してください)

[Answer]: A

---

## 質問 2 — パッケージ構成

コードのパッケージ構成はどうしますか？

A) 単一パッケージ（`podcast_downloader/core/` と `podcast_downloader/gui/` を1つの `pyproject.toml` で管理）

B) 2つの独立したパッケージ（`podcast_downloader_core/` と `podcast_downloader_gui/` を別々に管理）

C) Other (以下に記述してください)

[Answer]: A

---

## 生成チェックリスト

- [x] `unit-of-work.md` — ユニット定義と責務
- [x] `unit-of-work-dependency.md` — 依存関係マトリクス
- [x] `unit-of-work-story-map.md` — 機能とユニットのマッピング
