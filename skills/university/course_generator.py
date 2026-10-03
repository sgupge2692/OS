#!/usr/bin/env python3
"""Course Generator (v1)

科目フォルダを標準構成で作成する RyotaOS の Skill。

使い方:
    python skills/university/course_generator.py "machine learning"
    python skills/university/course_generator.py "機械学習" --slug machine_learning
"""

import argparse
import re
import sys
from pathlib import Path

SUBDIRS = [
    "lectures",
    "audio",
    "transcripts",
    "notes",
    "assignments",
    "anki",
    "exams",
]

# skills/university/course_generator.py -> リポジトリルート
REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_DIR = REPO_ROOT / "data" / "university"


def to_slug(name: str) -> str:
    """ASCII の科目名を machine_learning 形式に変換する。"""
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug


def create_course(name: str, slug: str | None = None) -> Path:
    slug = slug or to_slug(name)
    if not slug or not re.fullmatch(r"[a-z0-9_]+", slug):
        raise ValueError(
            f"'{name}' からフォルダ名を作れません。--slug machine_learning のように英数字で指定してください。"
        )

    course_dir = BASE_DIR / slug
    if course_dir.exists():
        raise FileExistsError(f"既に存在します: {course_dir}")

    for sub in SUBDIRS:
        d = course_dir / sub
        d.mkdir(parents=True)
        # 空フォルダもGitで追跡できるようにする
        (d / ".gitkeep").touch()

    return course_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="科目フォルダを標準構成で生成する")
    parser.add_argument("name", help="科目名(例: 'machine learning' / '機械学習')")
    parser.add_argument("--slug", help="フォルダ名(英数字とアンダースコア)。日本語の科目名では必須")
    args = parser.parse_args()

    try:
        course_dir = create_course(args.name, args.slug)
    except (ValueError, FileExistsError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    print(f"作成しました: {course_dir}")
    for sub in SUBDIRS:
        print(f"  ├ {sub}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
