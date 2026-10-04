#!/usr/bin/env python3
"""Course Generator (v2)

科目フォルダを標準構成で作成し、config/courses.json に科目名とフォルダ名を登録する。
登録済みの科目は、ファイル名から判定できる(--resolve)。

使い方:
    python3 skills/university/course_generator.py "マルチメディア情報処理"
        → フォルダ名を聞かれる(科目ごとに初回のみ)
    python3 skills/university/course_generator.py "機械学習" --slug machine_learning
    python3 skills/university/course_generator.py --resolve "マルチメディア情報処理第２回.mp4"
        → 該当する科目のフォルダ名を表示(見つからなければ終了コード 1)
"""

import argparse
import json
import re
import sys
import unicodedata
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
COURSES_FILE = REPO_ROOT / "config" / "courses.json"

SLUG_RE = re.compile(r"[a-z0-9_]+")
# 科目名のあとに続いてよい文字(「第1回」「_2」「 2」など)
BOUNDARY_RE = re.compile(r"[\s_\-(#第0-9]")


def normalize(s: str) -> str:
    """全角・半角の違いをそろえる(「第１回」と「第1回」を同じに扱う)。"""
    return unicodedata.normalize("NFKC", s).strip()


def load_courses() -> list[dict]:
    if not COURSES_FILE.exists():
        return []
    with open(COURSES_FILE, encoding="utf-8") as f:
        return json.load(f)["courses"]


def save_courses(courses: list[dict]) -> None:
    COURSES_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = COURSES_FILE.with_suffix(".json.part")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"courses": courses}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(COURSES_FILE)


def find_course(name: str, courses: list[dict]) -> dict | None:
    key = normalize(name)
    for c in courses:
        if normalize(c["name"]) == key:
            return c
    return None


def resolve_course(filename: str, courses: list[dict] | None = None) -> dict | None:
    """ファイル名から科目を判定する。見つからなければ None(推測しない)。"""
    courses = load_courses() if courses is None else courses
    stem = normalize(Path(filename).stem)
    best, best_len = None, -1
    for c in courses:
        n = normalize(c["name"])
        if not stem.startswith(n):
            continue
        rest = stem[len(n):]
        if rest and not BOUNDARY_RE.match(rest):
            continue
        if len(n) > best_len:
            best, best_len = c, len(n)
    return best


def to_slug(name: str) -> str:
    """ASCII の科目名を machine_learning 形式に変換する(日本語は空になる)。"""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def decide_slug(name: str, courses: list[dict], slug_arg: str | None) -> tuple[str, bool]:
    """フォルダ名を決める。戻り値は (slug, 登録済みかどうか)。"""
    registered = find_course(name, courses)
    if registered:
        if slug_arg and slug_arg != registered["slug"]:
            raise ValueError(f"'{name}' は既に '{registered['slug']}' として登録されています")
        return registered["slug"], True

    slug = slug_arg or to_slug(name)
    if not slug:
        if not sys.stdin.isatty():
            raise ValueError("フォルダ名を決められません。--slug machine_learning のように指定してください")
        slug = input("フォルダ名(英数字とアンダースコア): ").strip()

    if not SLUG_RE.fullmatch(slug):
        raise ValueError(f"フォルダ名は英数字とアンダースコアだけにしてください: '{slug}'")
    if any(c["slug"] == slug for c in courses):
        raise ValueError(f"フォルダ名 '{slug}' は別の科目で使われています")
    return slug, False


def create_course(name: str, slug_arg: str | None = None) -> tuple[Path, list[str], bool]:
    """科目フォルダを作り、未登録なら courses.json に登録する。

    既にあるフォルダや中身には触れず、足りないサブフォルダだけを作る。
    戻り値は (科目フォルダ, 新しく作ったサブフォルダ, 新しく登録したか)。
    """
    courses = load_courses()
    slug, registered = decide_slug(name, courses, slug_arg)

    course_dir = BASE_DIR / slug
    created = []
    for sub in SUBDIRS:
        d = course_dir / sub
        if not d.exists():
            d.mkdir(parents=True)
            # 空フォルダもGitで追跡できるようにする
            (d / ".gitkeep").touch()
            created.append(sub)

    newly_registered = False
    if not registered:
        courses.append({"name": name, "slug": slug})
        save_courses(courses)
        newly_registered = True

    return course_dir, created, newly_registered


def main() -> int:
    parser = argparse.ArgumentParser(description="科目フォルダの作成・登録と、ファイル名からの科目判定")
    parser.add_argument("name", nargs="?", help="科目名(例: 'マルチメディア情報処理')")
    parser.add_argument("--slug", help="フォルダ名(英数字とアンダースコア)。省略すると聞かれる")
    parser.add_argument("--resolve", metavar="FILENAME", help="ファイル名から科目を判定し、フォルダ名を表示する")
    args = parser.parse_args()

    if args.resolve:
        course = resolve_course(args.resolve)
        if course is None:
            print(f"該当する科目がありません: {args.resolve}", file=sys.stderr)
            return 1
        print(course["slug"])
        return 0

    if not args.name:
        parser.error("科目名を指定してください(または --resolve を使ってください)")

    try:
        course_dir, created, newly_registered = create_course(args.name, args.slug)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    if created or newly_registered:
        print(f"作成しました: {course_dir}")
        for sub in created:
            print(f"  ├ {sub}/")
        if newly_registered:
            print(f"登録しました: {COURSES_FILE.relative_to(REPO_ROOT)}")
    else:
        print(f"変更なし: 既に作成・登録済みです: {course_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
