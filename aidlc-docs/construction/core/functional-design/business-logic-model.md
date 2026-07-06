# ビジネスロジックモデル — Unit 1: core

## 1. RSSフィード取得・解析フロー

```
fetch_and_parse(url: str) -> list[Episode]
│
├─ HTTP GET url（タイムアウト: 30秒）
│   └─ ネットワークエラー → RSSFetchError を送出
│
├─ feedparser.parse(content)
│   └─ 解析失敗 → RSSParseError を送出
│
└─ フィードエントリごとに:
    ├─ enclosure から audio_url を抽出
    │   └─ audio_url が欠損 → このエントリをスキップ（BR-02-1）
    ├─ title 取得（欠損時: "（タイトルなし）"）（BR-02-2）
    ├─ published 取得・UTC変換（欠損時: None）（BR-02-3）
    ├─ description / summary 取得（欠損時: ""）（BR-02-4）
    ├─ itunes:duration → duration_parser.parse_duration()（BR-03-x）
    ├─ guid 取得（欠損時: audio_url をフォールバック）
    └─ Episode オブジェクト生成
        └─ guid 重複チェック → 重複時はスキップ（BR-02-5）
```

---

## 2. Durationパースロジック

```
parse_duration(raw: str) -> int | None

入力パターン:
  "3600"      → 3600秒（純粋な数値）
  "60:00"     → 3600秒（MM:SS）
  "1:00:00"   → 3600秒（HH:MM:SS）
  "90:30"     → 5430秒（MM > 60 でも時間に繰り上げ）（BR-03-3）
  ""  / None  → None
  その他       → None（BR-03-2）

format_duration(seconds: int | None) -> str

  None        → "不明"
  0〜59       → "SS秒"（例: "45秒"）
  60〜3599    → "MM分SS秒"（例: "45分30秒"）
  3600〜      → "HH時間MM分SS秒"（例: "1時間30分00秒"）（BR-03-5）
```

---

## 3. ファイル命名ロジック

```
build_filename(episode: Episode, feed: Feed) -> str

1. date_str = episode.published.strftime("%Y%m%d") if published else "00000000"（BR-04-5）
2. ext = Path(urlparse(episode.audio_url).path).suffix or ".mp3"（BR-04-2）
3. raw_name = f"{feed.label}_{date_str}_{episode.title}{ext}"
4. sanitized = re.sub(r'[/\\:*?"<>|]', '_', raw_name)（BR-04-3）
5. bytes_limit = 255
   while len(sanitized.encode('utf-8')) > bytes_limit:
       # タイトル部分を1文字ずつ切り詰める（BR-04-4）
       ...
6. return sanitized
```

---

## 4. ダウンロードフロー

```
DownloadManager.enqueue(episode, dest_dir, callbacks)
│
├─ [スロット空き待ち] 同時実行数 < 5（BR-08-x）
│
└─ threading.Thread で実行:
    ├─ filename = build_filename(episode, feed)
    ├─ dest_path = Path(dest_dir) / filename
    │
    ├─ [重複チェック] dest_path.exists()（BR-05-x）
    │   └─ 存在する → on_complete(episode, str(dest_path)) でスキップ通知
    │
    ├─ episode.status = DOWNLOADING
    │
    ├─ HTTP GET audio_url（ストリーミング）
    │   └─ エラー → 一時ファイル削除（BR-06-1）
    │              → episode.status = ERROR（BR-06-2）
    │              → on_error(episode, message)
    │
    ├─ チャンク書き込みループ（8192 bytes/chunk）
    │   ├─ キャンセルフラグ確認
    │   │   └─ キャンセル → 一時ファイル削除（BR-06-1）
    │   │                  → episode.status = NOT_DOWNLOADED（BR-06-2）
    │   └─ on_progress(episode, percent) コールバック
    │
    └─ 完了
        ├─ episode.status = DOWNLOADED
        └─ on_complete(episode, str(dest_path))
```

---

## 5. キャッシュ更新フロー

```
アプリ起動時（BR-09-1）:
  登録フィードごとに QThread でバックグラウンド fetch_and_parse()
  → 既存キャッシュと guid でマージ（BR-09-3）
    ├─ 既存エピソード: status / local_path を保持し、他フィールドを更新
    └─ 新規エピソード: status = NOT_DOWNLOADED で追加
  → save_episode_cache()
  → エラー時: 既存キャッシュを維持しエラー通知（BR-09-4）

手動更新（BR-09-2）:
  同上（QThread バックグラウンドで即時実行）
```

---

## 6. 設定管理フロー

```
起動時:
  config_dir() → OS別パス解決
    Windows: %APPDATA%\podcast-downloader\
    macOS:   ~/Library/Application Support/podcast-downloader/
    Linux:   ~/.config/podcast-downloader/

  load():
    settings.json が存在 → デシリアライズ → AppSettings
    存在しない → AppSettings(デフォルト値) を返す（BR-07-3 対応）
    JSON破損   → デフォルト値で起動・エラー通知（BR-07-3）

  load_episode_cache(feed_id):
    cache/{feed_id}.json が存在 → list[Episode] を返す
    存在しない → [] を返す

終了時・設定変更時:
  save(settings):
    config_dir が存在しなければ作成（BR-07-4）
    JSON シリアライズ → settings.json に書き込み（アトミック書き込み）

  save_episode_cache(feed_id, episodes):
    cache/ ディレクトリを作成（存在しなければ）
    JSON シリアライズ → cache/{feed_id}.json に書き込み
```
