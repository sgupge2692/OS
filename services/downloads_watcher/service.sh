#!/bin/bash
# Downloads Watcher を launchd に登録して常駐させる
#
# 使い方:
#   services/downloads_watcher/service.sh install     登録して起動(ログイン時に自動起動)
#   services/downloads_watcher/service.sh uninstall   停止して登録解除
#   services/downloads_watcher/service.sh status      状態を表示
#   services/downloads_watcher/service.sh logs        ログを表示(Ctrl+C で終了)

set -eu

LABEL="com.ryotaos.downloads-watcher"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$DIR/../.." && pwd)"
SCRIPT="$DIR/downloads_watcher.sh"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$REPO/logs"
LOG_FILE="$LOG_DIR/downloads_watcher.log"
DOMAIN="gui/$(id -u)"

install_service() {
    mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"
    chmod +x "$SCRIPT"

    cat > "$PLIST" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>10</integer>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
</dict>
</plist>
PLISTEOF

    # 既に登録済みなら一度外してから登録し直す
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$PLIST"
    echo "登録しました: $LABEL"
    echo "ログ: $LOG_FILE"
}

uninstall_service() {
    launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
    rm -f "$PLIST"
    echo "登録を解除しました: $LABEL"
}

status_service() {
    if launchctl print "$DOMAIN/$LABEL" > /tmp/ryotaos_watcher_status.txt 2>&1; then
        grep -E "state =|pid =|last exit code" /tmp/ryotaos_watcher_status.txt || true
    else
        echo "登録されていません"
    fi
}

case "${1:-}" in
    install)   install_service ;;
    uninstall) uninstall_service ;;
    status)    status_service ;;
    logs)      tail -f "$LOG_FILE" ;;
    *) echo "使い方: $0 {install|uninstall|status|logs}" >&2; exit 1 ;;
esac
