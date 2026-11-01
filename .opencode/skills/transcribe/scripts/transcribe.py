#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["faster-whisper>=1.1"]
# ///
"""Transcribe audio/video to text locally with faster-whisper (no API key).

Usage:
    uv run transcribe.py <file|folder>... [--lang ca|es|en|multi|auto] [--model medium]
                         [--prompt "names, acronyms"] [--format txt,srt] [--out DIR]
                         [--print] [--trash-source] [--to-mp3]

faster-whisper decodes m4a/mp4/ogg/wav... directly, so there is no need to
convert to mp3 first. If it cannot read the file, it converts it to wav with
ffmpeg in a temporary folder that is deleted afterwards. `--to-mp3` only also
saves an mp3 copy.

`--print` writes no file: the text goes in the JSON `text` field.
`--trash-source` sends the original to the macOS Trash on success.

Progress on stderr; on stdout one JSON line per file with the result.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AUDIO_EXTS = {"mp3", "m4a", "mp4", "ogg", "opus", "wav", "webm", "mov", "flac", "aac", "mkv"}
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
# None = autodetect; "multi" = per-segment detection (mixed ca+es meetings).
LANGUAGES = {"auto": None, "multi": None, "ca": "ca", "es": "es", "en": "en"}
FORMATS = {"txt", "srt"}


def log(msg: str, end: str = "\n") -> None:
    print(msg, file=sys.stderr, end=end, flush=True)


def collect_files(paths: list[str]) -> list[Path]:
    """Expand folders (non-recursive) and filter by audio/video extension."""
    files: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if p.is_dir():
            files.extend(
                sorted(
                    (f for f in p.iterdir() if f.is_file() and f.suffix.lower().lstrip(".") in AUDIO_EXTS),
                    key=lambda f: f.name.lower(),
                )
            )
        elif p.is_file():
            files.append(p)
        else:
            log(f"Does not exist: {p}")
    return files


def resolve_collision(path: Path) -> Path:
    """If `path` already exists, return a variant with ' (n)' that does not collide."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    n = 1
    while True:
        candidate = path.with_name(f"{stem} ({n}){suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def ffmpeg(src: Path, dst: Path, codec_args: list[str]) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found in PATH. Install it with: brew install ffmpeg")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
           "-vn", *codec_args, str(dst)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg failed without an error message.")


def to_mp3(src: Path, dst: Path) -> None:
    ffmpeg(src, dst, ["-c:a", "libmp3lame", "-b:a", "192k"])


def trash(src: Path) -> None:
    """Send `src` to the Trash and delete the attachment folder if left empty."""
    result = subprocess.run(["/usr/bin/trash", str(src)], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Could not move to the Trash: {result.stderr.strip()}")
    parent = src.parent
    if parent.parent.name == "attachments" and not any(parent.iterdir()):
        parent.rmdir()


def _srt_timestamp(seconds: float) -> str:
    total_ms = round(seconds * 1000)
    hours, rem_ms = divmod(total_ms, 3_600_000)
    minutes, rem_ms = divmod(rem_ms, 60_000)
    secs, millis = divmod(rem_ms, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_txt(segments, dst: Path) -> None:
    text = "\n".join(segment.text.strip() for segment in segments)
    dst.write_text(text + "\n", encoding="utf-8")


def write_srt(segments, dst: Path) -> None:
    lines = []
    for i, segment in enumerate(segments, start=1):
        lines.append(str(i))
        lines.append(f"{_srt_timestamp(segment.start)} --> {_srt_timestamp(segment.end)}")
        lines.append(segment.text.strip())
        lines.append("")
    dst.write_text("\n".join(lines), encoding="utf-8")


def transcribe(model, src: Path, lang: str, prompt: str | None):
    """Transcribe `src` showing the percentage on stderr; returns (segments, info).

    If PyAV cannot decode the file, convert it to wav in a temporary folder
    that is deleted automatically afterwards.
    """
    from faster_whisper import decode_audio

    try:
        audio = decode_audio(str(src))
    except Exception:  # noqa: BLE001 - any decoding error → ffmpeg
        log("  Could not read directly; converting to temporary wav with ffmpeg")
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "audio.wav"
            ffmpeg(src, wav, ["-ac", "1", "-ar", "16000"])
            audio = decode_audio(str(wav))
    segments_gen, info = model.transcribe(
        audio,
        language=LANGUAGES[lang],
        multilingual=lang == "multi",
        initial_prompt=prompt,
        vad_filter=True,
        beam_size=5,
    )
    segments = []
    for segment in segments_gen:
        segments.append(segment)
        if info.duration:
            log(f"\r  {min(segment.end / info.duration, 1.0) * 100:5.1f}%", end="")
    log("\r  100.0%")
    return segments, info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe audio/video to text locally (faster-whisper).")
    parser.add_argument("paths", nargs="+", help="Audio/video files or folders")
    parser.add_argument("--model", default="medium", choices=WHISPER_MODELS)
    parser.add_argument("--lang", default="auto", choices=list(LANGUAGES))
    parser.add_argument("--format", default="txt", help="Comma-separated formats: txt,srt")
    parser.add_argument("--out", help="Output folder (default: each file's own folder)")
    parser.add_argument("--prompt", help="Context for Whisper: proper nouns, acronyms, topic")
    parser.add_argument("--print", dest="print_text", action="store_true",
                        help="Write no files; the text goes in the stdout JSON")
    parser.add_argument("--trash-source", action="store_true",
                        help="Send the original to the Trash on success")
    parser.add_argument("--to-mp3", action="store_true", help="Also save an mp3 copy")
    args = parser.parse_args()
    args.formats = [f.strip() for f in args.format.split(",") if f.strip()]
    unknown = set(args.formats) - FORMATS
    if unknown or not args.formats:
        parser.error(f"Invalid formats: {', '.join(sorted(unknown)) or '(none)'}. Options: txt, srt")
    return args


def main() -> int:
    args = parse_args()
    files = collect_files(args.paths)
    if not files:
        log("No audio/video file found.")
        return 1

    out_dir = Path(args.out).expanduser() if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    # Deferred import: faster-whisper is heavy to load.
    from faster_whisper import WhisperModel

    log(f"Loading model {args.model}... (the first run downloads it to ~/.cache/huggingface)")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    failures = 0
    for src in files:
        dest_dir = out_dir or src.parent
        result: dict = {"src": str(src), "outputs": []}
        log(f"Transcribing {src.name}")
        try:
            if args.to_mp3 and not args.print_text and src.suffix.lower() != ".mp3":
                mp3 = resolve_collision(dest_dir / f"{src.stem}.mp3")
                to_mp3(src, mp3)
                result["outputs"].append(str(mp3))
            segments, info = transcribe(model, src, args.lang, args.prompt)
            if args.print_text:
                result["text"] = "\n".join(segment.text.strip() for segment in segments)
            else:
                for fmt in args.formats:
                    dst = resolve_collision(dest_dir / f"{src.stem}.{fmt}")
                    (write_txt if fmt == "txt" else write_srt)(segments, dst)
                    result["outputs"].append(str(dst))
            result.update(status="ok", language=info.language, duration=round(info.duration, 1))
            if args.trash_source:
                trash(src)
                result["trashed"] = True
        except Exception as e:  # noqa: BLE001 - report any error per file
            failures += 1
            result.update(status="error", error=str(e)[:500])
            log(f"  ERROR: {e}")
        print(json.dumps(result, ensure_ascii=False), flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
