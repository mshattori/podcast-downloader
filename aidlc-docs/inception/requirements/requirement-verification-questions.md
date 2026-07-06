# Requirements Clarification Questions

RSSポッドキャストダウンローダーツールの要件を明確にするための質問です。
各質問の `[Answer]:` タグの後に回答の文字（A、B、C...）を記入してください。
いずれも選択肢が合わない場合は最後の "Other" を選び、説明を追記してください。

---

## Question 1
どのOSで動作させますか？

A) Windows のみ

B) macOS のみ

C) Linux のみ

D) クロスプラットフォーム（Windows / macOS / Linux すべて）

E) Other (please describe after [Answer]: tag below)

[Answer]: D

---

## Question 2
GUIフレームワークの好みはありますか？

A) Python + Tkinter（標準ライブラリ、追加インストール不要）

B) Python + PyQt6 / PySide6（リッチなUI）

C) Python + wxPython

D) Electron（Web技術ベース、Node.js）

E) Other (please describe after [Answer]: tag below)

[Answer]: E

それぞれの Pros/Cons を考慮して、最適なフレームワークを選定する必要があります。

---

## Question 3
RSSフィードのURLはどのように指定しますか？

A) 起動時に1つのURLを設定ファイルやテキストフィールドに入力する

B) 複数のURLを登録・管理できる（フィード管理機能）

C) 毎回起動時にURLを入力する（設定保存なし）

D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 4
ダウンロード先フォルダはどのように決めますか？

A) アプリ起動時にフォルダ選択ダイアログで指定

B) 設定画面で保存先フォルダを事前設定

C) ダウンロードごとに毎回フォルダを選択

D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 5
コンテンツ一覧に表示する項目はどれですか？（複数選択可 → 該当するすべての文字を記入）

A) タイトル

B) 公開日時

C) オーディオの長さ（時間・分・秒）

D) 概要（description）

E) ダウンロード済み/未済のステータス

F) Other (please describe after [Answer]: tag below)

[Answer]: A, B, C, D, E

---

## Question 6
ダウンロード機能について、どの粒度で操作できると良いですか？

A) 一覧から1エピソードずつ選んでダウンロード

B) 複数エピソードを選択して一括ダウンロード

C) A と B 両方（個別 + 一括）

D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 7
オーディオの長さはどこから取得しますか？

A) RSSフィードのメタデータ（`<itunes:duration>` タグ等）から取得

B) ダウンロード後に実際のオーディオファイルを解析して取得

C) A を優先し、なければ B にフォールバック

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 8
ダウンロード中の進捗表示は必要ですか？

A) はい — プログレスバーまたは進捗率を表示したい

B) いいえ — ダウンロード完了の通知だけで十分

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 9 — Security Extension
Should security extension rules be enforced for this project?

A) Yes — enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)

B) No — skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)

X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 10 — Resiliency Extension
Should the resiliency baseline be applied to this project?

A) Yes — apply the resiliency baseline as directional best practices and design-time guidance

B) No — skip the resiliency baseline (suitable for PoCs, prototypes, and experimental projects where rapid iteration matters more than reliability)

X) Other (please describe after [Answer]: tag below)

[Answer]: X

resiliencey baseline とは何ですか？説明なしに質問されても意味が分かりません。

---

## Question 11 — Property-Based Testing Extension
Should property-based testing (PBT) rules be enforced for this project?

A) Yes — enforce all PBT rules as blocking constraints

B) Partial — enforce PBT rules only for pure functions and serialization round-trips

C) No — skip all PBT rules (suitable for simple CRUD applications, UI-only projects, or thin integration layers)

X) Other (please describe after [Answer]: tag below)

[Answer]: X

これも、説明なしに質問されても意味が分かりません。PBT とは何ですか？
