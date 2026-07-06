# ユニットテスト実行手順

## テスト対象

| テストファイル | テスト対象 | テスト数 |
|---|---|---|
| `tests/test_duration_parser.py` | `core/duration_parser.py` | 16 |
| `tests/test_settings_manager.py` | `core/settings_manager.py` | 10 |
| `tests/test_rss_parser.py` | `core/rss_parser.py` | 13 |
| `tests/test_downloader.py` | `core/downloader.py` | 6 |
| **合計** | | **45** |

> **注**: GUIコンポーネント（`gui/` 配下）のユニットテストは、QApplication が必要なため統合テストとして実施します。

---

## 実行手順

### 1. 全ユニットテストを実行

```bash
cd /home/mshattori/Dev/AI-DLC-work
pytest tests/ -v
```

### 2. モジュール別に実行

```bash
# duration_parser のみ
pytest tests/test_duration_parser.py -v

# settings_manager のみ
pytest tests/test_settings_manager.py -v

# rss_parser のみ
pytest tests/test_rss_parser.py -v

# downloader のみ
pytest tests/test_downloader.py -v
```

### 3. カバレッジレポート付きで実行

```bash
pip install pytest-cov
pytest tests/ --cov=podcast_downloader/core --cov-report=term-missing
```

---

## 期待される結果

```
==================== test session starts ====================
collected 45 items

tests/test_duration_parser.py ..............   [31%]
tests/test_settings_manager.py ..........     [53%]
tests/test_rss_parser.py .............        [82%]
tests/test_downloader.py ......               [100%]

==================== 45 passed in X.XXs ====================
```

---

## テスト失敗時の対応

1. 失敗したテスト名とエラーメッセージを確認する
2. 対応するソースコードを修正する
3. 再度テストを実行して全件パスを確認する

**よくある失敗原因**:
- `test_settings_manager.py`: ファイルシステムの権限問題 → `tmp_path` フィクスチャを使用しているため通常は発生しない
- `test_rss_parser.py`: `requests` のモックが正しく当たっていない → `pytest-mock` がインストールされているか確認
- `test_downloader.py`: スレッドタイムアウト → CI 環境ではタイムアウト値を延ばす場合がある
