最新 2 つのフィーチャースナップショット間の差分を自然言語化し、設計意図ドキュメント（`docs/design-intent.md`）に追記する。

## 引数

`$ARGUMENTS` は省略可能。
- 空の場合：`docs/snapshots/` 内で最も新しい 2 つの JSON ファイルを自動選択する
- 指定する場合：`{BEFORE_TIMESTAMP} {AFTER_TIMESTAMP}` の形式（例: `2026-05-28_16-23 2026-05-28_18-21`）

## 手順

### 1. スナップショットの特定

`docs/snapshots/` 内の `*-features.json` ファイルを名前順でリストアップする：
```bash
ls docs/snapshots/*-features.json 2>/dev/null | sort
```

**引数が空の場合：** 末尾の 2 件を `BEFORE_FILE`（古い方）と `AFTER_FILE`（新しい方）として使用する。

**引数が指定されている場合：** 指定されたタイムスタンプに対応するファイルを使用する：
- `BEFORE_FILE`: `docs/snapshots/{BEFORE_TIMESTAMP}-features.json`
- `AFTER_FILE`: `docs/snapshots/{AFTER_TIMESTAMP}-features.json`

ファイルが 2 件未満の場合はユーザーに「スナップショットが 2 件以上必要です。先に `/snapshot` を実行してください」と伝えて処理を終了する。

### 2. タイムスタンプの確定

```bash
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M")
```

また、`AFTER_FILE` のファイル名からタイムスタンプを取得し `AFTER_TIMESTAMP` として保持する（例：`2026-05-28_18-21`）。

### 3. 差分 JSON の生成

以下の Bash コマンドで差分 JSON を生成し `/tmp/diff-{TIMESTAMP}.json` に保存する：

```bash
python3 scripts/diff_features.py \
  --before "$BEFORE_FILE" \
  --after  "$AFTER_FILE" \
  > /tmp/diff-${TIMESTAMP}.json
```

### 4. 差分の解釈と自然言語サマリーの生成

`/tmp/diff-{TIMESTAMP}.json` の内容を読み込み、設計変更の概要を日本語で 1〜3 文に要約する（Claude 自身が実施）。

要約の観点：
- 追加・削除されたフィーチャーの設計上の意味（単純な追加なのか、既存形状の置き換えなのか）
- 変更されたパラメータが示す設計意図（サイズ変更、形状変更など）
- 全体的なモデルの進化の方向性

生成したサマリーを `SUMMARY` 変数として保持する。

### 5. 設計意図ドキュメントへの追記

以下の Bash コマンドで `docs/design-intent.md` にエントリを追記する：

```bash
python3 scripts/design_doc.py \
  --diff-file "/tmp/diff-${TIMESTAMP}.json" \
  --timestamp "$AFTER_TIMESTAMP" \
  --summary "$SUMMARY" \
  --doc-file "docs/design-intent.md"
```

### 6. 完了報告と設計意図の記述促進

ユーザーに以下を報告する：
- 比較したスナップショットのペア（BEFORE_FILE と AFTER_FILE のファイル名）
- 差分サマリー（追加・削除・変更の件数）
- `docs/design-intent.md` に追記したタイムスタンプ

さらに、`docs/design-intent.md` の該当エントリの `<!-- INTENT:START -->〜<!-- INTENT:END -->` 欄に、設計意図・変更の理由・今後の方針などを記述するよう促す。
