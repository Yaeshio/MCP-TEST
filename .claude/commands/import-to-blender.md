取得済みの STL ファイルを Blender にインポートして表示する。

## 引数

`$ARGUMENTS` は STL ファイルのパス。例：
`docs/stl/2026-06-01_12-00-model.stl`

`$ARGUMENTS` が空の場合は `docs/stl/` 内の最新ファイルを自動検出する。
ファイルが存在しない場合はユーザーへ先に `/export-stl` を実行するよう案内して処理を終了する。

## 手順

### 1. STL ファイルの特定

`$ARGUMENTS` が指定されていれば、そのパスを `stl_path` として使用する。

`$ARGUMENTS` が空の場合は Bash で以下を実行して最新ファイルを取得する：
```
ls -t docs/stl/*.stl 2>/dev/null | head -1
```
出力が空の場合は「`docs/stl/` に STL ファイルがありません。先に `/export-stl` を実行してください」とユーザーに伝えて処理を終了する。

### 2. ファイルの存在確認

`stl_path` に指定されたファイルが実際に存在するか確認する（`ls` または `test -f`）。
存在しない場合はユーザーに報告して処理を終了する。

### 3. Blender の起動

Bash で以下を実行する（`run_in_background: true` を指定してバックグラウンドで起動する）：
```
bash scripts/launch_blender.sh "{stl_path}"
```

`run_in_background: true` を使用することで、Blender の終了を待たずに次のステップへ進む。
スクリプトの開始直後に終了コードが取得できる場合のみエラーを確認する。
よくあるエラーと対処：
- `blender not found` → Blender をインストールして PATH に追加するよう案内する

### 4. 完了報告

Blender の起動コマンドを発行した時点でスキルを終了し、ユーザーに以下を報告する：
- 起動した STL ファイルのパス
- Blender をバックグラウンドで起動したこと（スキルは終了済みであること）
- 作業完了後はファイルメニューから手動で `.blend` 保存が可能なこと

報告後、追加の処理は行わずスキルを終了する。
