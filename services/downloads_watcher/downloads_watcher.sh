#!/bin/bash
# Downloads Watcher V2
# Downloads に落ちた mp4 を fswatch で検知し、ダウンロード完了後に m4a へ変換して振り分ける。
#
# 使い方:
#   services/downloads_watcher/downloads_watcher.sh
# 前提: brew install fswatch ffmpeg

set -u

DOWNLOADS="${DOWNLOADS:-$HOME/Downloads}"
COURSE_DIR="${COURSE_DIR:-$HOME/Desktop/02_University/3年後期の資料とか課題/マルチメディア情報処理}"
VIDEO_DIR="${VIDEO_DIR:-$COURSE_DIR/授業動画}"
AUDIO_DIR="${AUDIO_DIR:-$COURSE_DIR/音声}"
STABLE_SECS="${STABLE_SECS:-5}"   # この秒数ごとにサイズを見て、変化がなければ完了とみなす

for cmd in fswatch ffmpeg; do
    command -v "$cmd" >/dev/null 2>&1 || { echo "エラー: $cmd が見つかりません (brew install $cmd)" >&2; exit 1; }
done
mkdir -p "$VIDEO_DIR" "$AUDIO_DIR"

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
    local file="$1" base tmp out key
    [ "$(dirname "$file")" = "$DOWNLOADS" ] || return 0
    [ -f "$file" ] || return 0

    wait_until_stable "$file" || return 0

    # 同じファイル(同じサイズ)をスキップ済みなら、何も出さずに抜ける
    key="$file:$(stat -f%z "$file")"
    [ "${LAST_SKIPPED:-}" = "$key" ] && return 0

    base=$(basename "$file" .mp4)
    out="$AUDIO_DIR/$base.m4a"
    tmp="$AUDIO_DIR/$base.part.m4a"

    log "検知: $base"

    if [ -f "$out" ]; then
        LAST_SKIPPED="$key"
        log "スキップ: 音声が既にあります。動画は Downloads に残します ($base)"
        return 0
    fi

    log "変換開始: $base"
    if ffmpeg -nostdin -loglevel error -i "$file" -vn -c:a aac -b:a 128k "$tmp" -y; then
        mv "$tmp" "$out"
        mv "$file" "$VIDEO_DIR/"
        log "完了: $out"
    else
        rm -f "$tmp"
        log "失敗: $base (元の動画は Downloads に残しています)"
    fi
}
log "監視開始: $DOWNLOADS"

# 起動時にすでに溜まっている mp4 を先に処理
for f in "$DOWNLOADS"/*.mp4; do
    [ -e "$f" ] && process "$f"
done

# 以降は fswatch のイベントで処理(イベントは1件ずつ順番に処理される)
fswatch -0 -e '.*' -i '\.mp4$' "$DOWNLOADS" | while IFS= read -r -d '' f; do
    process "$f"
done
