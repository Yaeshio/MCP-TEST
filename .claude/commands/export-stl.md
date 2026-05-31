OnShape の Part Studio から STL ファイルをエクスポートして `docs/stl/` に保存する。

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

### 3. スキップ条件の確認

以下の条件に該当する場合は STL エクスポートをスキップし、理由をユーザーに伝えて処理を終了する：
- URL パスに `/assemblies/` が含まれる（アセンブリ形式は非対応）
- `wvm` が `m`（マイクロバージョン）の場合（Translation API は `w`/`v` のみ対応）

### 4. STL エクスポート（非同期 Translations API）

システムコマンド（`date +"%Y-%m-%d_%H-%M"`）で現在の日時を `TIMESTAMP` として取得する。

**Step 4-a. パーツ ID の取得**

`onshape_api_call` を以下の内容で呼び出す：
- `endpoint`: `getPartsWMVE`
- `path_params`: `{ "did": "{did}", "wvm": "{wvm}", "wvmid": "{wvmid}", "eid": "{eid}" }`

レスポンスは配列。各要素の `partId` フィールドを収集し、カンマ区切りの文字列 `partIdsStr` を組み立てる（例：`"JHK,JHD"`）。
パーツが 0 件の場合は「STL 取得不可（パーツなし）」としてユーザーに報告し処理を終了する。
エラーの場合は `partIdsStr` を空文字列として扱い、次のステップへ進む（`partIds` なしでフォールバック）。

**Step 4-b. 変換ジョブの作成**

`onshape_api_call` を以下の内容で呼び出す：
- `endpoint`: `createPartStudioTranslation`
- `path_params`: `{ "did": "{did}", "wv": "{wvm}", "wvid": "{wvmid}", "eid": "{eid}" }`
- `body`: `{ "formatName": "STL", "storeInDocument": false, "grouping": true, "unit": "millimeter", "partIds": "{partIdsStr}" }`

`partIdsStr` が空文字列の場合は `partIds` フィールドを body から省略する。
レスポンスから `id`（translation ID）を取得する。エラーの場合は「STL 取得不可（変換ジョブ失敗）」としてユーザーに報告し処理を終了する。

**Step 4-c. 完了ポーリング（最大 3 回）**

Bash で `sleep 5` を挟みながら、以下を最大 3 回繰り返す：
`onshape_api_call`：
- `endpoint`: `getTranslation`
- `path_params`: `{ "tid": "{translation_id}" }`

レスポンスの `requestState` が `"DONE"` になったらループを抜ける。
`"FAILED"` または 3 回経過した場合は「STL 取得不可（変換失敗 or タイムアウト）」としてユーザーに報告し処理を終了する。

**Step 4-d. STL データのダウンロード**

完了レスポンスの `resultExternalDataIds[0]` を `fid` として：
`onshape_api_call`：
- `endpoint`: `downloadExternalData`
- `path_params`: `{ "did": "{did}", "fid": "{fid}" }`

エラーの場合は「STL 取得不可（ダウンロード失敗）」としてユーザーに報告し処理を終了する。

### 5. ファイルの書き込み

`docs/stl/` ディレクトリが存在しない場合は作成する（`mkdir -p docs/stl`）。

Step 4-d のレスポンスボディをそのまま以下のパスに書き込む：
```
docs/stl/{TIMESTAMP}-model.stl
```

### 6. 完了報告

ユーザーに以下を報告する：
- STL ファイルの保存パス
- ファイルサイズ（`ls -lh` で確認）
- 単位: millimeter、モード: grouping
