#!/usr/bin/env python3
"""Generate an importable SRT from a video/audio file with mlx-whisper."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

import mlx_whisper


DEFAULT_MODEL = "mlx-community/whisper-small-mlx-q4"


def srt_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    whole = int(math.floor(seconds))
    millis = int(round((seconds - whole) * 1000))
    if millis == 1000:
        whole += 1
        millis = 0
    hours = whole // 3600
    minutes = (whole % 3600) // 60
    secs = whole % 60
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def extract_audio(media_path: Path, work_dir: Path) -> Path:
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_path = work_dir / f"{media_path.stem}.audio.16k.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i",
            str(media_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(audio_path),
        ],
        check=True,
    )
    return audio_path


def write_srt(result: dict, srt_path: Path) -> int:
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    blocks: list[str] = []
    index = 1
    for segment in result.get("segments", []):
        text = (segment.get("text") or "").strip()
        if not text:
            continue
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", start + 0.5))
        if end <= start:
            end = start + 0.5
        blocks.append(
            f"{index}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n{text}\n"
        )
        index += 1
    srt_path.write_text("\n".join(blocks), encoding="utf-8")
    return index - 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate SRT captions from media using mlx-whisper."
    )
    parser.add_argument("media", type=Path, help="Source video or audio file.")
    parser.add_argument("srt", type=Path, help="Output .srt path.")
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Directory for extracted audio and JSON. Defaults to <srt parent>/srt_work.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional raw Whisper JSON output path.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HF MLX Whisper model.")
    parser.add_argument("--language", default="zh", help="ASR language code.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    media_path = args.media.expanduser().resolve()
    srt_path = args.srt.expanduser().resolve()
    work_dir = (
        args.work_dir.expanduser().resolve()
        if args.work_dir
        else srt_path.parent / "srt_work"
    )
    audio_path = extract_audio(media_path, work_dir)
    result = mlx_whisper.transcribe(
        str(audio_path),
        path_or_hf_repo=args.model,
        language=args.language,
        task="transcribe",
    )
    json_path = (
        args.json_output.expanduser().resolve()
        if args.json_output
        else work_dir / f"{media_path.stem}.whisper.json"
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    count = write_srt(result, srt_path)
    print(f"audio={audio_path}")
    print(f"json={json_path}")
    print(f"srt={srt_path}")
    print(f"segments={count}")


if __name__ == "__main__":
    main()

