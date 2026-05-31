#!/usr/bin/env python3
"""
OnShape フィーチャースナップショット — Markdown ジェネレーター

Usage:
    python3 scripts/snapshot.py \
        --features-file <path> \
        --did <DID> --wvm <w|v|m> --wvmid <WVMID> --eid <EID> \
        --timestamp <YYYY-MM-DD_HH-MM> \
        [--json-output <path>] \
        [--output-dir docs/changelogs]

stdout: 書き込んだ Markdown ファイルのパス（1 行）
exit:   0=成功, 1=エラー
"""

import argparse
import json
import os
import re
import sys


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OnShape feature snapshot Markdown generator")
    p.add_argument("--features-file", required=True,
                   help="getPartStudioFeatures / getFeatures API レスポンスの JSON ファイルパス")
    p.add_argument("--did", required=True, help="OnShape ドキュメント ID")
    p.add_argument("--wvm", required=True, choices=["w", "v", "m"],
                   help="ワークスペース種別: w=workspace, v=version, m=microversion")
    p.add_argument("--wvmid", required=True, help="ワークスペース/バージョン/マイクロバージョン ID")
    p.add_argument("--eid", required=True, help="エレメント ID")
    p.add_argument("--timestamp", required=True,
                   help="タイムスタンプ (YYYY-MM-DD_HH-MM)")
    p.add_argument("--json-output", default=None,
                   help="生 JSON の保存先ファイルパス（省略時は保存しない）")
    p.add_argument("--output-dir", default="docs/changelogs",
                   help="Markdown 出力ディレクトリ（デフォルト: docs/changelogs）")

    args = p.parse_args()

    if not re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$", args.timestamp):
        print(f"ERROR: --timestamp は YYYY-MM-DD_HH-MM 形式で指定してください: {args.timestamp!r}",
              file=sys.stderr)
        sys.exit(1)

    return args


def load_response(path: str) -> dict:
    try:
        raw = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: ファイルを読み込めません: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON のパースに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    # MCP ツールが文字列として返した場合の二重デコード対策
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    if not isinstance(data, dict):
        print(f"ERROR: レスポンスが dict ではありません: {type(data)}", file=sys.stderr)
        sys.exit(1)

    return data


def extract_features(data: dict) -> list:
    # featureStates から featureId → featureStatus のマップを構築
    # suppressionState は実際の API では常に null のため featureStates を正とする
    status_map = {
        fid: state.get("featureStatus", "OK")
        for fid, state in data.get("featureStates", {}).items()
    }

    records = []
    for i, feat in enumerate(data.get("features", []), start=1):
        fid = feat.get("featureId", "")
        records.append({
            "idx": i,
            "name": feat.get("name", ""),
            "featureType": feat.get("featureType", ""),
            "featureId": fid,
            "suppressed": bool(feat.get("suppressed", False)),
            "featureStatus": status_map.get(fid, "OK"),
        })

    return records


def compute_stats(features: list) -> dict:
    unique_types = sorted({f["featureType"] for f in features})
    return {
        "total": len(features),
        "suppressed": sum(1 for f in features if f["suppressed"]),
        "error_count": sum(1 for f in features if f["featureStatus"] != "OK"),
        "unique_types": unique_types,
    }


def build_markdown(features: list, stats: dict, args: argparse.Namespace) -> str:
    # タイムスタンプ変換: "2026-05-28_18-21" → "2026-05-28 18:21" / "2026-05-28T18:21:00Z"
    date_part, time_part = args.timestamp.split("_")
    hh, mm = time_part.split("-")
    display_ts = f"{date_part} {hh}:{mm}"
    iso_ts = f"{date_part}T{hh}:{mm}:00Z"

    # フィーチャーテーブル行
    rows = "\n".join(
        f"| {f['idx']} | {f['name']} | {f['featureType']} | {f['featureStatus']} | {str(f['suppressed']).lower()} |"
        for f in features
    )
    table = (
        f"## フィーチャー一覧（{stats['total']} 件）\n\n"
        "| # | 名前 | タイプ | ステータス | 抑制 |\n"
        "|---|------|--------|-----------|------|\n"
        f"{rows}"
    )

    # サマリー
    types_str = ", ".join(stats["unique_types"]) if stats["unique_types"] else "（なし）"
    json_ref = f"`{args.json_output}`" if args.json_output else "（保存なし）"
    summary = (
        "## サマリー\n\n"
        f"- 合計フィーチャー数: {stats['total']}\n"
        f"- 抑制済み: {stats['suppressed']}\n"
        f"- エラーあり: {stats['error_count']} 件（featureStatus が \"OK\" 以外）\n"
        f"- 使用フィーチャータイプ: {types_str}\n"
        f"- 生データ JSON: {json_ref}"
    )

    # ドキュメント組み立て
    return "\n\n".join([
        f"# フィーチャースナップショット — {display_ts}",
        (
            f"**ドキュメント ID:** `{args.did}`  \n"
            f"**ワークスペース ID:** `{args.wvmid}` ({args.wvm})  \n"
            f"**エレメント ID:** `{args.eid}`  \n"
            f"**取得日時:** {iso_ts}"
        ),
        table,
        summary,
    ]) + "\n"


def write_output(content: str, output_dir: str, filename: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def save_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved: {path}", file=sys.stderr)


def main():
    args = parse_args()

    print(f"Loading features from: {args.features_file}", file=sys.stderr)
    data = load_response(args.features_file)

    if args.json_output:
        save_json(data, args.json_output)

    features = extract_features(data)
    print(f"Extracted {len(features)} features", file=sys.stderr)

    stats = compute_stats(features)
    print(
        f"Stats: total={stats['total']}, suppressed={stats['suppressed']}, errors={stats['error_count']}",
        file=sys.stderr,
    )

    md = build_markdown(features, stats, args)

    filename = f"{args.timestamp}-feature-snapshot.md"
    out_path = write_output(md, args.output_dir, filename)
    print(f"Written: {out_path}", file=sys.stderr)

    # stdout には出力パスのみ（スキルがキャプチャ）
    print(out_path)


if __name__ == "__main__":
    main()
