# Unit 2: gui — NFR要件計画

Unit 1（core）で確定したNFR（Python 3.11+・ログ・クロスプラットフォーム）を継承します。
GUI固有の未決定事項について1点確認します。

---

## 質問 1 — 翻訳ファイルの管理

OSロケールに従う国際化（i18n）を実装しますが、翻訳ファイルはどう管理しますか？

A) Qt の `.ts` / `.qm` ファイルを使う（`lupdate` / `lrelease` ツールで管理。標準的なQt方式）

B) Python の `gettext` / `.po` ファイルを使う（Pythonエコシステム標準）

C) まずは日本語ハードコードで実装し、i18n対応は後回しにする（シンプルに始める）

D) Other (以下に記述してください)

[Answer]: C 

---

## 生成チェックリスト

- [x] `nfr-requirements.md` — GUI固有の非機能要件
- [x] `tech-stack-decisions.md` — GUIライブラリ・ツール選定
