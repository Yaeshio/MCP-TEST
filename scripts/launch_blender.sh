#!/usr/bin/env bash
set -euo pipefail

STL_PATH="${1:-}"

# 引数なしの場合は docs/stl/ 内の最新 STL を自動検出
if [ -z "$STL_PATH" ]; then
    STL_PATH=$(ls -t docs/stl/*.stl 2>/dev/null | head -1 || true)
    if [ -z "$STL_PATH" ]; then
        echo "Error: No STL file found in docs/stl/. Run /export-stl first." >&2
        exit 1
    fi
fi

if [ ! -f "$STL_PATH" ]; then
    echo "Error: STL file not found: $STL_PATH" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STL_ABS="$(realpath "$STL_PATH")"

BLENDER_BIN=""

# ── WSL: Windows Blender を優先検索 ────────────────────────────────────────────
if grep -qi "microsoft" /proc/version 2>/dev/null; then
    WSL_BLENDER_BIN=""

    # 最新バージョンの blender.exe を選択（バージョン降順ソート）
    while IFS= read -r candidate_exe; do
        if [ -f "$candidate_exe" ]; then
            WSL_BLENDER_BIN="$candidate_exe"
            break
        fi
    done < <(
        for d in "/mnt/c/Program Files/Blender Foundation/Blender "*/; do
            [ -f "${d}blender.exe" ] && echo "${d}blender.exe"
        done | sort -V -r
    )

    # fallback: Windows の where コマンドで検索
    if [ -z "$WSL_BLENDER_BIN" ]; then
        WIN_PATH=$(cmd.exe /c "where blender" 2>/dev/null | head -1 | tr -d '\r' || true)
        if [ -n "$WIN_PATH" ]; then
            LINUX_PATH=$(wslpath -u "$WIN_PATH" 2>/dev/null || true)
            [ -f "$LINUX_PATH" ] && WSL_BLENDER_BIN="$LINUX_PATH"
        fi
    fi

    if [ -n "$WSL_BLENDER_BIN" ]; then
        WIN_STL=$(wslpath -w "$STL_ABS")
        WIN_SCRIPT=$(wslpath -w "$SCRIPT_DIR/blender_import_stl.py")
        echo "Launching Windows Blender with: $STL_ABS"
        nohup "$WSL_BLENDER_BIN" --python "$WIN_SCRIPT" -- --stl "$WIN_STL" &>/dev/null &
        disown
        exit 0
    fi
fi

# ── Linux / macOS フォールバック（既存ロジック）────────────────────────────────
for candidate in \
    "blender" \
    "/usr/bin/blender" \
    "/usr/local/bin/blender" \
    "/snap/bin/blender" \
    "$HOME/blender/blender" \
    "/Applications/Blender.app/Contents/MacOS/Blender"
do
    if command -v "$candidate" &>/dev/null 2>&1; then
        BLENDER_BIN="$candidate"
        break
    fi
done

if [ -z "$BLENDER_BIN" ]; then
    echo "Error: blender not found. Install Blender and add it to PATH." >&2
    exit 1
fi

echo "Launching Blender with: $STL_ABS"
nohup "$BLENDER_BIN" --python "$SCRIPT_DIR/blender_import_stl.py" -- --stl "$STL_ABS" &>/dev/null &
disown
exit 0
