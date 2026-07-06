# 機能とユニットのマッピング

ユーザーストーリーは本プロジェクトでスキップしたため、要件定義書（requirements.md）の機能要件（FR）をユニットにマッピングします。

## 機能要件 → ユニットマッピング

| 機能要件 | 説明 | Unit 1: core | Unit 2: gui |
|---|---|:---:|:---:|
| FR-01: RSSフィード管理 | 複数フィードURL登録・永続化 | `settings_manager` | `feed_panel` |
| FR-02: コンテンツ一覧表示 | エピソード一覧（タイトル・日時・長さ・概要・状態） | `rss_parser`, `models` | `episode_list` |
| FR-03: 音声長さ取得 | durationメタデータ取得・正規化 | `duration_parser`, `rss_parser` | — |
| FR-04: エピソードダウンロード | 複数選択一括ダウンロード・保存先設定 | `downloader`, `settings_manager` | `download_panel`, `feed_panel` |
| FR-05: ダウンロード進捗表示 | プログレスバー・完了/エラー通知 | `downloader`（コールバック） | `download_panel` |
| FR-06: 設定管理 | 保存先フォルダ・フィード管理の設定画面 | `settings_manager` | `settings_dialog` |

## ユニット別 機能カバレッジ

### Unit 1: core
- FR-01（設定永続化）
- FR-02（RSS解析・データモデル）
- FR-03（duration解析・フォーマット） ← **Unit 1のみで完結**
- FR-04（ダウンロードエンジン）
- FR-05（進捗コールバック）
- FR-06（設定読み書き）

### Unit 2: gui
- FR-01（フィード管理UI）
- FR-02（エピソード一覧表示）
- FR-04（ダウンロード操作UI）
- FR-05（進捗表示UI）
- FR-06（設定ダイアログ）

## 備考

- `duration_parser.py` は純粋関数のみで構成され、Unit 2 からの直接依存はない
- ダウンロード進捗の通知は Unit 1 のコールバック → Unit 2 の Qt Signal/Slot 経由で連携する
- フィードキャッシュ（エピソードのJSONキャッシュ）は Unit 1 の `settings_manager` が管理し、Unit 2 はその読み書きを呼び出すだけ
