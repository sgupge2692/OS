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
科目フォルダを標準構成(lectures, audio, transcripts, notes, assignments, anki, exams)で作成する。
```bash
python3 skills/university/course_generator.py "machine learning"
python3 skills/university/course_generator.py "機械学習" --slug machine_learning
```
- macOS では `python` ではなく `python3`
- 日本語の科目名は `--slug`(英数字とアンダースコア)が必須
- 既にある科目は上書きせずエラーで止まる

### Downloads Watcher (services/downloads_watcher)
Downloads の mp4 を検知し、m4a に変換して音声フォルダへ、動画は授業動画フォルダへ移す。
```bash
./services/downloads_watcher/downloads_watcher.sh   # 停止は Ctrl+C
```
- 変換先は `COURSE_DIR` / `VIDEO_DIR` / `AUDIO_DIR` の環境変数で変更できる
- 音声が既にある動画は、Downloads に残してスキップする

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
