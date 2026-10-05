
# RyotaOS

Personal Operating System

## Vision

Automate recurring tasks in:

- Study
- Fitness
- Career
- Development
- Knowledge Management

## Development Style

Usage Driven Development

Problem
↓
Issue
↓
Implementation
↓
Automation

## Workflow

Issue
↓
Branch
↓
Implementation
↓
Pull Request
↓
Review
↓
Merge

## コマンド集

### セットアップ
```bash
brew install fswatch ffmpeg
```

### Course Generator (skills/university)
科目フォルダを標準構成(lectures, audio, transcripts, notes, assignments, anki, exams)で作成し、`config/courses.json` に登録する。
```bash
python3 skills/university/course_generator.py "マルチメディア情報処理"   # フォルダ名を聞かれる(科目ごとに初回のみ)
python3 skills/university/course_generator.py "機械学習" --slug machine_learning
python3 skills/university/course_generator.py --resolve "マルチメディア情報処理第2回.mp4"   # 科目のフォルダ名を表示
```
- macOS では `python` ではなく `python3`
- 既にある科目は中身に触れず、足りないサブフォルダだけを作る
- `--resolve` は、ファイル名が登録済みの科目名で始まるときだけ一致(推測しない)。見つからなければ終了コード 1

### Downloads Watcher (services/downloads_watcher)
Downloads の mp4 を検知し、ファイル名から科目を判定して `data/university/<科目>/` に振り分ける(動画は lectures/、音声は audio/)。
```bash
./services/downloads_watcher/downloads_watcher.sh   # 手動で起動する場合。停止は Ctrl+C
```
- ファイル名が登録済みの科目名で始まる必要がある(例: `マルチメディア情報処理第3回.mp4`)。科目は Course Generator で先に登録する
- 判定できない動画は Downloads に残し、ログに理由を出す
- 音声が既にある動画も Downloads に残してスキップする
- 置き場は `DATA_DIR` 環境変数で変更できる(既定: `data/university`)

### 開発フロー
```bash
git checkout main
git fetch origin && git merge --ff-only origin/main
git checkout -b feature/<Issue番号>-<名前>
# 実装 → 動作確認
git add <ファイル>
git commit -m "feat: ... (#<Issue番号>)"
git push -u origin feature/<Issue番号>-<名前>
# GitHubでPR作成(本文に Closes #<Issue番号>)
```

### ファイルを探す
```bash
mdfind -name "ファイル名"
open -R <パス>   # Finderで表示
```

### Transcribe (skills/university)
音声ファイルをローカルで文字起こしして、.txt を出力する(Apple Silicon、mlx-whisper)。
```bash
source .venv/bin/activate    # ターミナルを開き直したときに毎回必要
python skills/university/transcribe.py data/university/<科目>/audio/<音声ファイル>.m4a
```
- 出力先は、音声が `audio/` にあれば隣の `transcripts/`、それ以外は音声と同じフォルダ(`--out-dir` で指定可)
- 既定のモデルは medium(1時間半の講義で約9分)。初回のみモデル(約1.5GB)をダウンロードする
- 出力は `[hh:mm:ss] 本文` の形式で、1行ずつ時刻が付く
- 出力済みの場合はスキップする(`--force` で上書き)

### 環境構築 (.venv)
```bash
brew install uv
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install mlx-whisper
```
- `python3 -m venv` は Python 3.14 で pip の導入に失敗したため、uv を使う

### Downloads Watcher の常駐化 (launchd)
```bash
./services/downloads_watcher/service.sh install     # 登録・起動(ログイン時に自動起動)
./services/downloads_watcher/service.sh status      # 状態確認
./services/downloads_watcher/service.sh logs        # ログを見る
./services/downloads_watcher/service.sh uninstall   # 解除
```
- ログは `logs/downloads_watcher.log`
- スクリプトを更新したら `install` をやり直す
- `Operation not permitted` が出たら、フルディスクアクセスに `/bin/bash` を追加する
