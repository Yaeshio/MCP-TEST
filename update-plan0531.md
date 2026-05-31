1. 現在、変更履歴とAPIからえられた生のJsonデータは同じファイルに同居している。
このとき、まずは生データの保存を行い、その後これを解析することで変更の差分を
自然言語としてドキュメント化する。この解析作業は自然言語としてドキュメント化を
行うためのものであるため、AIエージェントが行うものとする。

2. Stlファイル取得用の操作は別コマンドで実施するようにしたい。

3. 生Jsonの差分を解析して、設計意図を記述するドキュメントに
変更箇所を示し、これに変更箇所における設計意図などを記述する。


以下に、変更後のディレクトリ構造の例を示す。

.claude/commands/
  snapshot.md       ← 簡素化（フィーチャー取得のみ、生 JSON を別保存）
  export-stl.md     ← 新規（snapshot.md の 3-b を移設）
  review-diff.md    ← 新規（差分検出 → 自然言語化 → 設計意図ドキュメントへ）
scripts/
  snapshot.py       ← 改修（--json-output 追加、STL 引数削除）
  diff_features.py  ← 新規（2つの features.json を featureId キーで意味的 diff）
  design_doc.py     ← 新規（diff を設計意図ドキュメントへ反映、人間記述は温存）
docs/
  snapshots/        ← 新規（生 JSON、git 追跡）
  changelogs/       ← 既存（JSON 埋め込みを除いた軽量版）
  stl/              ← 既存
  design-intent.md  ← 新規（自動の差分記述 + 人間の意図、マーカーで分離）