# MCP-TEST

OnShape と Claude Code を MCP で接続し、変更履歴・スナップショットからドキュメントを自動生成・管理するプロジェクト。

## 構成

```
docs/
  changelogs/   # OnShape変更履歴から生成したドキュメント
  versions/     # バージョン・スナップショット情報
.mcp.json       # MCP サーバー設定（onshape-mcp）
```

## MCP 設定

- **onshape-mcp**: `npx --yes onshape-mcp` で起動
- 認証設定: `~/.config/onshape-mcp/config.toml`（APIキー方式）

## 利用方法

Claude Code で OnShape のドキュメントやバージョン情報を自然言語で取得できます。
