# Unit 1: core — コード生成計画

## ユニット情報

- **ユニット名**: core
- **コード出力先**: `/home/mshattori/Dev/AI-DLC-work/podcast_downloader/core/`
- **テスト出力先**: `/home/mshattori/Dev/AI-DLC-work/tests/`
- **プロジェクト設定**: `/home/mshattori/Dev/AI-DLC-work/pyproject.toml`
- **依存ユニット**: なし（Unit 2: gui が本ユニットに依存）

## 参照設計ドキュメント

- `aidlc-docs/construction/core/functional-design/domain-entities.md`
- `aidlc-docs/construction/core/functional-design/business-rules.md`
- `aidlc-docs/construction/core/functional-design/business-logic-model.md`
- `aidlc-docs/construction/core/nfr-requirements/tech-stack-decisions.md`
- `aidlc-docs/construction/core/nfr-design/nfr-design-patterns.md`
- `aidlc-docs/construction/core/nfr-design/logical-components.md`

---

## 生成ステップ

### Step 1: プロジェクト構造セットアップ
- [x] `pyproject.toml` を作成（依存関係定義）
- [x] `podcast_downloader/__init__.py` を作成
- [x] `podcast_downloader/core/__init__.py` を作成
- [x] `tests/__init__.py` を作成
- [x] `README.md` を作成（基本的なプロジェクト説明）

### Step 2: データモデル生成（`core/models.py`）
- [x] `DownloadStatus` 列挙型を実装
- [x] `Feed` データクラスを実装
- [x] `Episode` データクラスを実装
- [x] `AppSettings` データクラスを実装
- [x] JSON シリアライズ/デシリアライズメソッドを実装

### Step 3: Durationパーサー生成（`core/duration_parser.py`）
- [x] `parse_duration(raw)` 関数を実装（BR-03-x 準拠）
- [x] `format_duration(seconds)` 関数を実装（BR-03-5 準拠）

### Step 4: Durationパーサー ユニットテスト（`tests/test_duration_parser.py`）
- [x] `parse_duration` の正常系テスト（秒/MM:SS/HH:MM:SS フォーマット）
- [x] `parse_duration` の境界値テスト（0秒・巨大値・None・空文字）
- [x] `parse_duration` の異常系テスト（不正フォーマット）
- [x] `format_duration` のテスト（秒/分/時間各レンジ・None）

### Step 5: 設定マネージャー生成（`core/settings_manager.py`）
- [x] `SettingsManager` クラスを実装
- [x] OS 別設定ディレクトリ解決（`platformdirs` 使用）
- [x] `load()` / `save()` を実装（アトミック書き込みパターン）
- [x] `load_episode_cache()` / `save_episode_cache()` を実装
- [x] `config_dir()` を実装
- [x] フェイルセーフデフォルトパターンを実装（BR-07-3 準拠）

### Step 6: 設定マネージャー ユニットテスト（`tests/test_settings_manager.py`）
- [x] デフォルト設定での起動テスト
- [x] 設定の保存・読み込みラウンドトリップテスト
- [x] JSON 破損時のフェイルセーフテスト
- [x] エピソードキャッシュの保存・読み込みテスト
- [x] アトミック書き込みテスト（一時ファイルのクリーンアップ確認）

### Step 7: RSSパーサー生成（`core/rss_parser.py`）
- [x] カスタム例外クラス定義（`RSSFetchError` / `RSSParseError`）
- [x] `fetch_and_parse(url)` を実装（タイムアウト30秒）
- [x] `parse_feed_from_string(content)` を実装（テスト用）
- [x] エントリ→Episode 変換ロジックを実装（BR-02-x 準拠）
- [x] `audio_url` 欠損フィルタリングを実装
- [x] guid 重複排除を実装

### Step 8: RSSパーサー ユニットテスト（`tests/test_rss_parser.py`）
- [x] 正常な RSS フィードのパーステスト（フィクスチャ XML 使用）
- [x] `audio_url` 欠損エピソードの除外テスト
- [x] フィールド欠損時のデフォルト値テスト（BR-02-2〜4）
- [x] guid 重複排除テスト
- [x] ネットワークエラー時の `RSSFetchError` テスト（`requests` をモック）
- [x] 不正フォーマット時の `RSSParseError` テスト

### Step 9: ダウンロードエンジン生成（`core/downloader.py`）
- [x] `DownloadError` 例外クラスを実装
- [x] `DownloadManager` クラスを実装
- [x] `Semaphore(5)` によるスロット制御を実装（NFR設計パターン2）
- [x] `threading.Event` によるキャンセルフラグを実装
- [x] ファイル名生成ロジックを実装（BR-04-x 準拠）
- [x] ファイル存在チェック（重複スキップ）を実装（BR-05-x 準拠）
- [x] HTTP ストリーミングダウンロードを実装（8192 byte チャンク）
- [x] 中断時の一時ファイル削除を実装（BR-06-x 準拠）
- [x] `enqueue()` / `cancel()` / `cancel_all()` / `active_count()` を実装

### Step 10: ダウンロードエンジン ユニットテスト（`tests/test_downloader.py`）
- [x] ファイル名生成テスト（BR-04-x 各ルール）
- [x] ファイル存在時のスキップテスト（BR-05-x）
- [x] ダウンロード完了時のコールバックテスト（HTTP をモック）
- [x] エラー時の一時ファイル削除テスト（BR-06-x）
- [x] キャンセル動作テスト
- [x] 同時実行数制御テスト（セマフォ）

### Step 11: コードサマリードキュメント生成
- [x] `aidlc-docs/construction/core/code/code-summary.md` を作成（生成ファイル一覧・実装サマリー）

---

## 機能要件カバレッジ

| 機能要件 | 実装ステップ |
|---|---|
| FR-01: RSSフィード管理（永続化） | Step 5（settings_manager） |
| FR-02: エピソード一覧（RSS解析・モデル） | Step 2（models）+ Step 7（rss_parser） |
| FR-03: 音声長さ取得・表示 | Step 3（duration_parser） |
| FR-04: ダウンロード | Step 9（downloader） |
| FR-05: ダウンロード進捗（コールバック） | Step 9（downloader） |
| FR-06: 設定管理 | Step 5（settings_manager） |
