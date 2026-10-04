#!/bin/bash
# Downloads Watcher
# Downloads に落ちた mp4 を fswatch で検知し、ファイル名から科目を判定して
# data/university/<科目>/ に振り分ける(動画は lectures/、音声は audio/)。
# 科目を判定できない動画は Downloads に残す。
#
# 使い方:
#   services/downloads_watcher/downloads_watcher.sh
# 前提: brew install fswatch ffmpeg / 科目は course_generator.py で登録済みであること

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/../.." && pwd)"

DOWNLOADS="${DOWNLOADS:-$HOME/Downloads}"
DATA_DIR="${DATA_DIR:-$REPO/data/university}"
GENERATOR="$REPO/skills/university/course_generator.py"
PYTHON="${PYTHON:-python3}"
STABLE_SECS="${STABLE_SECS:-5}"   # この秒数ごとにサイズを見て、変化がなければ完了とみなす

for cmd in fswatch ffmpeg "$PYTHON"; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "エラー: $cmd が見つかりません" >&2; exit 1; }
done
[ -f "$GENERATOR" ] || { echo "エラー: $GENERATOR が見つかりません" >&2; exit 1; }

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ファイルサイズが変化しなくなるまで待つ(ダウンロード完了判定)
wait_until_stable() {
    local f="$1" prev=-1 cur
    while :; do
        [ -f "$f" ] || return 1
        cur=$(stat -f%z "$f")
        [ "$cur" = "$prev" ] && return 0
        prev=$cur
        sleep "$STABLE_SECS"
    done
}

process() {
    local file="$1" base slug video_dir audio_dir out tmp key
    # Downloads 直下の mp4 だけを対象にする
    [ "$(dirname "$file")" = "$DOWNLOADS" ] || return 0
    [ -f "$file" ] || return 0   # 処理済みで移動済みなら二重処理せずここで抜ける

    base=$(basename "$file" .mp4)

    # ファイル名から科目を判定する(見つからなければ触らない)
    if ! slug=$("$PYTHON" "$GENERATOR" --resolve "$file" 2>/dev/null); then
        key="unresolved:$file"
        if [ "${LAST_SKIPPED:-}" != "$key" ]; then
            LAST_SKIPPED="$key"
            log "科目を判定できません: $base (登録済みの科目名で始まるファイル名にしてください。動画は Downloads に残します)"
        fi
        return 0
    fi

    wait_until_stable "$file" || return 0

    video_dir="$DATA_DIR/$slug/lectures"
    audio_dir="$DATA_DIR/$slug/audio"
    out="$audio_dir/$base.m4a"
    tmp="$audio_dir/$base.part.m4a"

    # 同じファイル(同じサイズ)をスキップ済みなら、何も出さずに抜ける
    key="$file:$(stat -f%z "$file")"
    [ "${LAST_SKIPPED:-}" = "$key" ] && return 0

    log "検知: $base → $slug"

    if [ -f "$out" ]; then
        LAST_SKIPPED="$key"
        log "スキップ: 音声が既にあります。動画は Downloads に残します ($base)"
        return 0
    fi

    mkdir -p "$video_dir" "$audio_dir"
    log "変換開始: $base"
    # 途中で失敗しても完成扱いにならないよう、一時ファイルに書いてから改名する
    if ffmpeg -nostdin -loglevel error -i "$file" -vn -c:a aac -b:a 128k "$tmp" -y; then
        mv "$tmp" "$out"
        mv "$file" "$video_dir/"
        log "完了: $out"
    else
        rm -f "$tmp"
        log "失敗: $base (元の動画は Downloads に残しています)"
    fi
}

log "監視開始: $DOWNLOADS → $DATA_DIR"

# 起動時にすでに溜まっている mp4 を先に処理
for f in "$DOWNLOADS"/*.mp4; do
    [ -e "$f" ] && process "$f"
done

# 以降は fswatch のイベントで処理(イベントは1件ずつ順番に処理される)
fswatch -0 -e '.*' -i '\.mp4$' "$DOWNLOADS" | while IFS= read -r -d '' f; do
    process "$f"
done
