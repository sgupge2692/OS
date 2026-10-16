from pathlib import Path
import subprocess
import sys


def convert(video_path: str):
    video = Path(video_path)

    if not video.exists():
        print(f"File not found: {video}")
        return

    output = video.with_suffix(".m4a")

    print(f"Converting: {video.name}")

    subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(video),
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(output),
            "-y",
        ],
        check=True,
    )

    print(f"Created: {output}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("python3 video_to_audio.py <video_file>")
        sys.exit(1)

    convert(sys.argv[1])
