OnShape の Part Studio またはアセンブリからフィーチャースナップショットを取得し、変更履歴ドキュメントと生データ JSON を生成する。

## 引数

`$ARGUMENTS` は OnShape ドキュメントの URL。例：
`https://cad.onshape.com/documents/{did}/w/{wid}/e/{eid}`

`$ARGUMENTS` が空の場合は、環境変数 `$ONSHAPE_DOCUMENT_URL` をフォールバックとして使用する。
両方とも未設定の場合はユーザーへ URL の入力を求めてから処理を進める。

## 手順

### 1. URL のパース

URL から以下を抽出する：
- `did` — ドキュメント ID（`/documents/` と次の `/` の間）
- `wvm` — ワークスペース種別：`w`（ワークスペース）、`v`（バージョン）、`m`（マイクロバージョン）
- `wvmid` — `w`/`v`/`m` セグメントの直後にある ID
- `eid` — エレメント ID（`/e/` の後）

### 2. 認証確認

`onshape_auth_status` を `validate: true` で呼び出す。認証に失敗した場合は、`~/.config/onshape-mcp/config.toml` に正しい API キーを設定するよう案内して処理を中断する。

### 3. フィーチャー取得

`onshape_api_call` を以下の内容で呼び出す：
- `endpoint`: `getPartStudioFeatures`
- `path_params`: `{ "did": "{did}", "wvm": "{wvm}", "wvmid": "{wvmid}", "eid": "{eid}" }`
- `query_params`: `{ "rollbackBarIndex": "-1", "noSketchGeometry": "false" }`

アセンブリの場合（URL パスに `/assemblies/` が含まれる、または上記呼び出しが 400/404 を返す）は
以下の endpoint で再試行する：
- `endpoint`: `getFeatures`
- `path_params`: `{ "did": "{did}", "wvm": "{wvm}", "wvmid": "{wvmid}", "eid": "{eid}" }`
- `query_params`: `{ "rollbackBarIndex": "-1", "noSketchGeometry": "false" }`

### 4. スクリプトによるドキュメント生成

システムコマンド（`date +"%Y-%m-%d_%H-%M"`）で現在の日時を `TIMESTAMP` として取得する。

Step 3 のフィーチャーレスポンスのファイルパスを `FEATURES_FILE` として特定する：
- レスポンスが大きく Claude Code に自動保存された場合（ツール結果に「Output has been saved to ...」と表示）: そのファイルパスをそのまま `FEATURES_FILE` として使用する
- レスポンスがインコンテキストで返った場合: Write ツールで `/tmp/onshape-features-{TIMESTAMP}.json` に保存し、そのパスを `FEATURES_FILE` として使用する

以下の Bash コマンドを実行し、Markdown スナップショットと生 JSON を生成する：

```bash
MD_PATH=$(python3 scripts/snapshot.py \
  --features-file "$FEATURES_FILE" \
  --did "{did}" --wvm "{wvm}" --wvmid "{wvmid}" --eid "{eid}" \
  --timestamp "$TIMESTAMP" \
  --json-output "docs/snapshots/${TIMESTAMP}-features.json")
```

スクリプトの stdout に出力されたパスが `MD_PATH`（例: `docs/changelogs/2026-05-28_18-21-feature-snapshot.md`）として使用される。

### 5. 完了報告

ユーザーに以下を報告する：
- Markdown ファイルパス、フィーチャー数・エラー数
- 生データ JSON の保存先: `docs/snapshots/{TIMESTAMP}-features.json`

### 6. 次のアクションの提案

`featureStatus` が OK 以外のフィーチャーがある場合は、その名前を列挙し、OnShape 上での確認を促す。

スナップショットが 2 件以上蓄積されている場合は、`/review-diff` コマンドで差分を確認して設計意図ドキュメントを更新できることを案内する。

STL ファイルが必要な場合は、`/export-stl` コマンドを案内する。
