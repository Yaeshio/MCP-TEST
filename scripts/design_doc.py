#!/usr/bin/env python3
"""
設計意図ドキュメント更新スクリプト

diff_features.py の出力 JSON を受け取り、docs/design-intent.md に
新しいエントリ（自動生成セクション + 人間記述欄）を追記する。
既存の ENTRY ブロックは一切変更しない。

Usage:
    python3 scripts/design_doc.py \
        --diff-file <diff.json のパス> \
        --timestamp <YYYY-MM-DD_HH-MM> \
        [--summary <Claude が生成した自然言語サマリー>] \
        [--doc-file docs/design-intent.md]

exit: 0=成功, 1=エラー
"""

import argparse
import json
import os
import re
import sys


def extract_param_value(json_str: str) -> str:
    """BTMParameter JSON 文字列から人間向けの値を返す"""
    try:
        obj = json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return str(json_str)
    bt = obj.get("btType", "")
    if "BTMParameterQuantity" in bt:
        return obj.get("expression", str(obj))
    if "BTMParameterString" in bt:
        return obj.get("value", str(obj))
    if "BTMParameterLookupTablePath" in bt:
        val = obj.get("value", {})
        if isinstance(val, dict):
            parts = [val.get("size", ""), val.get("pitch", ""), val.get("type", "")]
            return " / ".join(p for p in parts if p)
        return str(val)
    if "BTMParameterBoolean" in bt or "BTMParameterEnum" in bt:
        return str(obj.get("value", str(obj)))
    return obj.get("expression", obj.get("value", str(obj)))


def normalize_param_id(pid: str) -> str:
    """V2/V3 などのバージョンサフィックスを除去して正規化する"""
    return re.sub(r"V\d+$", "", pid)


HEADER = "# 設計意図ドキュメント\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="設計意図ドキュメント更新")
    p.add_argument("--diff-file", required=True, help="diff_features.py の出力 JSON")
    p.add_argument("--timestamp", required=True, help="タイムスタンプ (YYYY-MM-DD_HH-MM)")
    p.add_argument("--summary", default="", help="Claude が生成した自然言語サマリー（省略可）")
    p.add_argument("--doc-file", default="docs/design-intent.md",
                   help="更新対象の設計意図ドキュメント（デフォルト: docs/design-intent.md）")

    args = p.parse_args()

    if not re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$", args.timestamp):
        print(f"ERROR: --timestamp は YYYY-MM-DD_HH-MM 形式で指定してください: {args.timestamp!r}",
              file=sys.stderr)
        sys.exit(1)

    return args


def load_diff(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        print(f"ERROR: ファイルを読み込めません: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: diff JSON のパースに失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


def format_auto_section(diff: dict, summary: str) -> str:
    """AUTO セクションの本文を生成する"""
    lines = []

    if summary:
        lines.append(summary)
        lines.append("")

    added = diff.get("added", [])
    removed = diff.get("removed", [])
    modified = diff.get("modified", [])
    unchanged = diff.get("unchanged_count", 0)

    if added:
        lines.append(f"### 追加 ({len(added)} 件)")
        for f in added:
            lines.append(f"- **{f['name']}** ({f['featureType']}) — featureId: `{f['featureId']}`")
        lines.append("")

    if removed:
        lines.append(f"### 削除 ({len(removed)} 件)")
        for f in removed:
            lines.append(f"- **{f['name']}** ({f['featureType']}) — featureId: `{f['featureId']}`")
        lines.append("")

    if modified:
        lines.append(f"### 変更 ({len(modified)} 件)")
        for f in modified:
            changes = f.get("changes", {})
            change_parts = []
            for key in ("name", "featureType", "suppressed"):
                if key in changes:
                    bv = changes[key]["before"]
                    av = changes[key]["after"]
                    change_parts.append(f"`{key}`: {bv!r} → {av!r}")
            if "parameters" in changes:
                seen: dict[str, tuple[str, str]] = {}
                for pid, chg in changes["parameters"].items():
                    base = normalize_param_id(pid)
                    bv = extract_param_value(chg["before"])
                    av = extract_param_value(chg["after"])
                    if base not in seen:
                        seen[base] = (bv, av)
                        change_parts.append(f"`{base}`: {bv} → {av}")
            desc = "、".join(change_parts) if change_parts else "変更あり"
            lines.append(f"- **{f['name']}** ({f['featureType']}) — {desc}")
        lines.append("")

    if not added and not removed and not modified:
        lines.append("変更なし（フィーチャー構成は前回スナップショットと同一）")
        lines.append("")

    lines.append(f"変更なし: {unchanged} 件")

    return "\n".join(lines)


def build_entry(timestamp: str, auto_body: str) -> str:
    """新しい ENTRY ブロックを生成する"""
    date_part, time_part = timestamp.split("_")
    hh, mm = time_part.split("-")
    display_ts = f"{date_part} {hh}:{mm}"

    return (
        f"<!-- ENTRY:{timestamp} -->\n"
        f"## 変更 {display_ts}\n\n"
        f"<!-- AUTO:START -->\n"
        f"{auto_body}\n"
        f"<!-- AUTO:END -->\n\n"
        f"<!-- INTENT:START -->\n"
        f"\n"
        f"<!-- INTENT:END -->\n"
        f"<!-- /ENTRY:{timestamp} -->"
    )


def load_or_init_doc(path: str) -> str:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return HEADER + "\n"


def entry_exists(content: str, timestamp: str) -> bool:
    return f"<!-- ENTRY:{timestamp} -->" in content


def insert_entry(content: str, entry: str) -> str:
    """ヘッダー直後に新しいエントリを挿入する（最新が先頭になるよう）"""
    if content.startswith(HEADER):
        rest = content[len(HEADER):]
        return HEADER + "\n" + entry + "\n\n" + rest.lstrip("\n")
    # ヘッダーがない場合は先頭に追加
    return HEADER + "\n" + entry + "\n\n" + content


def main():
    args = parse_args()

    diff = load_diff(args.diff_file)
    auto_body = format_auto_section(diff, args.summary)
    entry = build_entry(args.timestamp, auto_body)

    content = load_or_init_doc(args.doc_file)

    if entry_exists(content, args.timestamp):
        print(f"INFO: {args.timestamp} のエントリは既に存在します。スキップします。", file=sys.stderr)
        print(args.doc_file)
        return

    updated = insert_entry(content, entry)

    os.makedirs(os.path.dirname(os.path.abspath(args.doc_file)), exist_ok=True)
    with open(args.doc_file, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"Written: {args.doc_file}", file=sys.stderr)
    print(args.doc_file)


if __name__ == "__main__":
    main()
