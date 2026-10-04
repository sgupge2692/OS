#!/usr/bin/env python3
"""Transcribe (v1)

音声ファイル(m4a など)をローカルで文字起こしして .txt を出力する。
Apple Silicon 上で mlx-whisper を使う(外部 API 不要)。

出力先:
    音声が「音声」フォルダにある場合は、その隣の「文字起こし」フォルダ。
    それ以外は音声と同じフォルダ。--out-dir で指定もできる。

使い方:
    python skills/university/transcribe.py <音声ファイル>
    python skills/university/transcribe.py <音声ファイル> --out-dir <出力フォルダ>
    python skills/university/transcribe.py <音声ファイル> --model mlx-community/whisper-small-mlx
    python skills/university/transcribe.py <音声ファイル> --force   # 出力済みでも上書き
"""

import argparse
import sys
from pathlib import Path

DEFAULT_MODEL = "mlx-community/whisper-medium-mlx"


def fmt_time(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def default_out_dir(audio: Path) -> Path:
    if audio.parent.name == "音声":
        return audio.parent.parent / "文字起こし"
    return audio.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="音声を文字起こしして txt を出力する")
    parser.add_argument("audio", type=Path, help="音声ファイルのパス")
    parser.add_argument("--out-dir", type=Path, help="出力フォルダ (既定: 音声の隣の「文字起こし」)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"モデル (既定: {DEFAULT_MODEL})")
    parser.add_argument("--force", action="store_true", help="出力済みでも上書きする")
    args = parser.parse_args()

    audio = args.audio.expanduser().resolve()
    if not audio.is_file():
        print(f"エラー: ファイルが見つかりません: {audio}", file=sys.stderr)
        return 1

    out_dir = args.out_dir.expanduser().resolve() if args.out_dir else default_out_dir(audio)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{audio.stem}.txt"

    if out.exists() and not args.force:
        print(f"スキップ: 既に存在します: {out}")
        return 0

    try:
        import mlx_whisper
    except ImportError:
        print("エラー: mlx-whisper が入っていません (uv pip install mlx-whisper)", file=sys.stderr)
        return 1

    print(f"文字起こし開始: {audio.name} (モデル: {args.model})")
    result = mlx_whisper.transcribe(
        str(audio),
        path_or_hf_repo=args.model,
        language="ja",
    )

    # 一時ファイルに書いてから改名(途中で失敗しても完成扱いにしない)
    tmp = out_dir / f"{audio.stem}.txt.part"
    with open(tmp, "w", encoding="utf-8") as f:
        for seg in result["segments"]:
            f.write(f"[{fmt_time(seg['start'])}] {seg['text'].strip()}\n")
    tmp.rename(out)

    print(f"完了: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
