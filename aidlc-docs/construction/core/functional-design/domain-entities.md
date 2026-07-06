# ドメインエンティティ定義 — Unit 1: core

## Feed（RSSフィード）

| フィールド | 型 | 必須 | 説明 |
|---|---|:---:|---|
| `id` | `str` (UUID4) | ✅ | 一意識別子（アプリ側で生成） |
| `url` | `str` | ✅ | RSSフィードURL（http/https） |
| `label` | `str` | ✅ | ユーザーが付けた名前（表示用） |
| `last_fetched` | `datetime \| None` | — | 最後にRSS取得した日時（UTC） |

**不変条件**:
- `url` は空文字不可
- `label` は空文字不可（未設定時は URL のドメイン部分をデフォルト値とする）
- `id` は生成後に変更しない

---

## Episode（エピソード）

| フィールド | 型 | 必須 | 説明 |
|---|---|:---:|---|
| `id` | `str` (UUID4) | ✅ | 一意識別子（feed_id + guid のハッシュ） |
| `feed_id` | `str` | ✅ | 所属するフィードの ID |
| `guid` | `str` | ✅ | RSS フィードの guid 値（重複排除用） |
| `title` | `str` | ✅ | エピソードタイトル |
| `published` | `datetime \| None` | — | 公開日時（UTC）。欠損時は `None` |
| `duration_seconds` | `int \| None` | — | 音声の長さ（秒）。欠損時は `None` |
| `duration_display` | `str` | ✅ | 表示用文字列（例: `1時間30分00秒`、欠損時は `不明`） |
| `description` | `str` | ✅ | 概要テキスト（欠損時は空文字） |
| `audio_url` | `str` | ✅ | ダウンロード対象のオーディオURL |
| `status` | `DownloadStatus` | ✅ | ダウンロード状態（デフォルト: `NOT_DOWNLOADED`） |

**除外ルール**: `audio_url` が欠損または空のエピソードはパース時点で除外し、`Episode` オブジェクトを生成しない。

**不変条件**:
- `guid` はフィード内で一意（重複時は後者を無視）
- `status` は `DownloadStatus` 列挙値のみ取り得る

---

## DownloadStatus（ダウンロード状態）

```
NOT_DOWNLOADED  # 未ダウンロード（デフォルト）
DOWNLOADING     # ダウンロード進行中
DOWNLOADED      # ダウンロード完了
ERROR           # ダウンロードエラー
```

**状態遷移**:
```
NOT_DOWNLOADED ──→ DOWNLOADING ──→ DOWNLOADED
                        │
                        └──→ ERROR ──→ NOT_DOWNLOADED（再試行時）
```

---

## AppSettings（アプリ設定）

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `feeds` | `list[Feed]` | `[]` | 登録済みフィード一覧 |
| `download_dir` | `str` | OS のダウンロードフォルダ | ダウンロード先ディレクトリ |
| `max_concurrent_downloads` | `int` | `5` | 同時ダウンロード上限（固定値、変更不可） |
| `window_geometry` | `dict \| None` | `None` | ウィンドウ位置・サイズ（x, y, width, height） |

**不変条件**:
- `download_dir` は存在するディレクトリのパスであること（保存時にディレクトリ作成を試みる）
- `max_concurrent_downloads` は常に 5（変更不可）

---

## エンティティ関係

```
AppSettings
    └── feeds: list[Feed] (1対多)

Feed
    └── episodes: list[Episode]  ※キャッシュファイルに保存（AppSettingsには含まない）

Episode
    └── feed_id → Feed.id
```

**永続化の分離**:
- `AppSettings`（フィード一覧含む）→ `settings.json`
- `Episode` 一覧（フィードごと）→ `cache/{feed_id}.json`
