# ビルド手順書

## 前提条件

| 項目 | 要件 |
|---|---|
| Python | 3.11 以上 |
| pip | 23.0 以上 |
| 対応OS | Windows 10+, macOS 12+, Ubuntu 22.04+ |
| ディスク空き容量 | 500 MB 以上（PySide6 含む） |

---

## 手順

### 1. 依存関係のインストール

```bash
# プロジェクトルートで実行
cd /home/mshattori/Dev/AI-DLC-work

# 通常インストール（アプリ実行のみ）
pip install -e .

# 開発用（テストツール含む）
pip install -e ".[dev]"
```

### 2. 動作確認（起動テスト）

```bash
python main.py
```

正常起動すれば、GUIウィンドウが表示されます。

### 3. ビルド成果物の確認

| 成果物 | 場所 |
|---|---|
| アプリパッケージ | `podcast_downloader/` |
| コアモジュール | `podcast_downloader/core/*.py` |
| GUIモジュール | `podcast_downloader/gui/*.py` |
| エントリーポイント | `main.py` |
| 設定・依存定義 | `pyproject.toml` |

### 4. トラブルシューティング

**PySide6 のインストールが失敗する場合**
```bash
# pip を最新版に更新してから再試行
pip install --upgrade pip
pip install -e ".[dev]"
```

**`platformdirs` が見つからない場合**
```bash
pip install platformdirs
```

**Windows で `os.replace` がエラーになる場合**
- ウイルス対策ソフトがファイル操作をブロックしている可能性があります
- 一時的に除外設定を追加してください

---

## 環境変数（オプション）

| 変数 | 値 | 効果 |
|---|---|---|
| `PODCAST_DL_DEBUG` | `1` | ログレベルを DEBUG に設定（詳細ログ出力） |
