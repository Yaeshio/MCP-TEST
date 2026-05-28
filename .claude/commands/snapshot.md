OnShape の Part Studio またはアセンブリからフィーチャースナップショットを取得し、変更履歴ドキュメントを生成する。

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

### 3. フィーチャー取得 と STL エクスポート（並行実行）

以下の 2 つの `onshape_api_call` を **同時に** 呼び出す：

**3-a. フィーチャー取得**
`onshape_api_call` を以下の内容で呼び出す：
- `endpoint`: `getPartStudioFeatures`
- `path_params`: `{ "did": "{did}", "wvm": "{wvm}", "wvmid": "{wvmid}", "eid": "{eid}" }`
- `query_params`: `{ "rollbackBarIndex": "-1", "noSketchGeometry": "false" }`

アセンブリの場合（URL パスに `/assemblies/` が含まれる、または上記呼び出しが 400/404 を返す）は
以下の endpoint で再試行する：
- `endpoint`: `getFeatures`
- `path_params`: `{ "did": "{did}", "wvm": "{wvm}", "wvmid": "{wvmid}", "eid": "{eid}" }`
- `query_params`: `{ "rollbackBarIndex": "-1", "noSketchGeometry": "false" }`

**3-b. STL エクスポート（Part Studio・非同期 Translations API）**

アセンブリの場合、または 3-a がアセンブリパスで再試行された場合はこのステップ全体をスキップする。
`wvm` が `m`（マイクロバージョン）の場合もスキップする（Translation API は `w`/`v` のみ対応）。

以下を順に実行する：

**Step 3-b-0. パーツ ID の取得**
`onshape_api_call` を以下の内容で呼び出す：
- `endpoint`: `getPartsWMVE`
- `path_params`: `{ "did": "{did}", "wvm": "{wvm}", "wvmid": "{wvmid}", "eid": "{eid}" }`

レスポンスは配列。各要素の `partId` フィールドを収集し、カンマ区切りの文字列 `partIdsStr` を組み立てる（例：`"JHK,JHD"`）。
パーツが 0 件の場合はこのステップ全体をスキップし「STL 取得不可（パーツなし）」として扱う。
エラーの場合は `partIdsStr` を空文字列として扱い、次のステップへ進む（`partIds` なしでフォールバック）。

**Step 3-b-1. 変換ジョブの作成**
`onshape_api_call` を以下の内容で呼び出す：
- `endpoint`: `createPartStudioTranslation`
- `path_params`: `{ "did": "{did}", "wv": "{wvm}", "wvid": "{wvmid}", "eid": "{eid}" }`
- `body`: `{ "formatName": "STL", "storeInDocument": false, "grouping": true, "unit": "millimeter", "partIds": "{partIdsStr}" }`

`partIdsStr` が空文字列の場合は `partIds` フィールドを body から省略する。
レスポンスから `id`（translation ID）を取得する。エラーの場合はスキップし「STL 取得不可」として扱う。

**Step 3-b-2. 完了ポーリング（最大 3 回）**
Bash で `sleep 5` を挟みながら、以下を最大 3 回繰り返す：
`onshape_api_call`：
- `endpoint`: `getTranslation`
- `path_params`: `{ "tid": "{translation_id}" }`

レスポンスの `requestState` が `"DONE"` になったらループを抜ける。
`"FAILED"` または 3 回経過した場合はスキップし「STL 取得不可（変換失敗 or タイムアウト）」として扱う。

**Step 3-b-3. STL データのダウンロード**
完了レスポンスの `resultExternalDataIds[0]` を `fid` として：
`onshape_api_call`：
- `endpoint`: `downloadExternalData`
- `path_params`: `{ "did": "{did}", "fid": "{fid}" }`

エラーの場合はスキップし「STL 取得不可（ダウンロード失敗）」として扱う。

### 4. スクリプトによるドキュメント生成

システムコマンド（`date +"%Y-%m-%d_%H-%M"`）で現在の日時を `TIMESTAMP` として取得する。

3-a のフィーチャーレスポンスのファイルパスを `FEATURES_FILE` として特定する：
- レスポンスが大きく Claude Code に自動保存された場合（ツール結果に「Output has been saved to ...」と表示）: そのファイルパスをそのまま `FEATURES_FILE` として使用する
- レスポンスがインコンテキストで返った場合: Write ツールで `/tmp/onshape-features-{TIMESTAMP}.json` に保存し、そのパスを `FEATURES_FILE` として使用する

以下の Bash コマンドを実行し、Markdown スナップショットを生成する：

**STL 取得成功の場合：**
```bash
MD_PATH=$(python3 scripts/snapshot.py \
  --features-file "$FEATURES_FILE" \
  --did "{did}" --wvm "{wvm}" --wvmid "{wvmid}" --eid "{eid}" \
  --timestamp "$TIMESTAMP" \
  --stl-file "docs/stl/${TIMESTAMP}-model.stl")
```

**STL 取得不可の場合：**
```bash
MD_PATH=$(python3 scripts/snapshot.py \
  --features-file "$FEATURES_FILE" \
  --did "{did}" --wvm "{wvm}" --wvmid "{wvmid}" --eid "{eid}" \
  --timestamp "$TIMESTAMP" \
  --stl-unavailable-reason "{取得不可の理由}")
```

スクリプトの stdout に出力されたパスが `MD_PATH`（例: `docs/changelogs/2026-05-28_18-21-feature-snapshot.md`）として使用される。

### 5. ファイルの書き込み

**5-a. Markdown スナップショット**

Step 4 のスクリプトが `$MD_PATH` に書き込み済み。追加の書き込みは不要。

**5-b. STL ファイル（取得成功時のみ）**

`docs/stl/` ディレクトリが存在しない場合は作成する（`mkdir -p docs/stl`）。
3-b のレスポンスボディをそのまま以下のパスに書き込む：
```
docs/stl/{YYYY-MM-DD}_{HH-MM}-model.stl
```

書き込み後、ユーザーに以下を報告する：
- Markdown ファイルパスとフィーチャー数・エラー数
- STL ファイルパス（取得成功時）または取得不可の理由（スキップ時）

### 6. 次のアクションの提案

`featureStatus` が OK 以外のフィーチャーがある場合は、その名前を列挙し、OnShape 上での確認を促す。
