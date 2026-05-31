#!/usr/bin/env python3
"""
OnShape フィーチャー差分検出スクリプト

2 つの features.json を featureId キーで比較し、差分を JSON で出力する。

Usage:
    python3 scripts/diff_features.py \
        --before docs/snapshots/{OLD_TS}-features.json \
        --after  docs/snapshots/{NEW_TS}-features.json

stdout: 差分 JSON
exit:   0=成功, 1=エラー
"""

import argparse
import json
import sys


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="OnShape feature diff")
    p.add_argument("--before", required=True, help="比較元の features.json パス")
    p.add_argument("--after", required=True, help="比較先の features.json パス")
    return p.parse_args()


def load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        print(f"ERROR: ファイルを読み込めません: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON のパースに失敗しました ({path}): {e}", file=sys.stderr)
        sys.exit(1)

    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            pass

    if not isinstance(data, dict):
        print(f"ERROR: レスポンスが dict ではありません: {type(data)}", file=sys.stderr)
        sys.exit(1)

    return data


def index_features(data: dict) -> dict:
    """featureId → feature オブジェクト のマップを返す"""
    return {f["featureId"]: f for f in data.get("features", []) if f.get("featureId")}


def extract_params(feature: dict) -> dict:
    """parameterId → value の辞書を返す（比較用）"""
    result = {}
    for param in feature.get("parameters", []):
        pid = param.get("parameterId")
        if not pid:
            continue
        # 値は message 内の value フィールドを優先、なければ全体を文字列化
        msg = param.get("message", {})
        val = msg.get("value") if isinstance(msg, dict) else None
        if val is None:
            val = json.dumps(param, ensure_ascii=False, sort_keys=True)
        result[pid] = val
    return result


def diff_feature(before: dict, after: dict) -> dict | None:
    """2 つの feature を比較し、変化があれば diff 情報を返す。同じなら None。"""
    changes = {}

    for key in ("name", "featureType", "suppressed"):
        bv = before.get(key)
        av = after.get(key)
        if bv != av:
            changes[key] = {"before": bv, "after": av}

    before_params = extract_params(before)
    after_params = extract_params(after)

    param_changes = {}
    all_param_ids = set(before_params) | set(after_params)
    for pid in sorted(all_param_ids):
        bv = before_params.get(pid)
        av = after_params.get(pid)
        if bv != av:
            param_changes[pid] = {"before": bv, "after": av}

    if param_changes:
        changes["parameters"] = param_changes

    if not changes:
        return None

    return {
        "featureId": after.get("featureId", before.get("featureId")),
        "name": after.get("name", before.get("name")),
        "featureType": after.get("featureType", before.get("featureType")),
        "changes": changes,
    }


def main():
    args = parse_args()

    before_data = load_json(args.before)
    after_data = load_json(args.after)

    before_map = index_features(before_data)
    after_map = index_features(after_data)

    before_ids = set(before_map)
    after_ids = set(after_map)

    added = [
        {
            "featureId": fid,
            "name": after_map[fid].get("name", ""),
            "featureType": after_map[fid].get("featureType", ""),
        }
        for fid in (after_ids - before_ids)
    ]

    removed = [
        {
            "featureId": fid,
            "name": before_map[fid].get("name", ""),
            "featureType": before_map[fid].get("featureType", ""),
        }
        for fid in (before_ids - after_ids)
    ]

    modified = []
    unchanged_count = 0
    for fid in before_ids & after_ids:
        diff = diff_feature(before_map[fid], after_map[fid])
        if diff:
            modified.append(diff)
        else:
            unchanged_count += 1

    # 順序を安定させる（name でソート）
    added.sort(key=lambda x: x["name"])
    removed.sort(key=lambda x: x["name"])
    modified.sort(key=lambda x: x["name"])

    result = {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged_count": unchanged_count,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
