#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["faster-whisper>=1.1"]
# ///
"""Transcriu àudio/vídeo a text en local amb faster-whisper (sense clau API).

Ús:
    uv run transcribe.py <fitxer|carpeta>... [--lang ca|es|en|auto] [--model medium]
                         [--format txt,srt] [--out DIR] [--to-mp3]

faster-whisper descodifica m4a/mp4/ogg/wav... directament, així que no cal
convertir a mp3 abans. `--to-mp3` només desa també una còpia en mp3 (ffmpeg).

Progrés a stderr; a stdout una línia JSON per fitxer amb el resultat.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

AUDIO_EXTS = {"mp3", "m4a", "mp4", "ogg", "opus", "wav", "webm", "mov", "flac", "aac", "mkv"}
WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v3"]
LANGUAGES = {"auto": None, "ca": "ca", "es": "es", "en": "en"}
FORMATS = {"txt", "srt"}


def log(msg: str, end: str = "\n") -> None:
    print(msg, file=sys.stderr, end=end, flush=True)


def collect_files(paths: list[str]) -> list[Path]:
    """Expandeix carpetes (no recursiu) i filtra per extensió d'àudio/vídeo."""
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
            log(f"No existeix: {p}")
    return files


def resolve_collision(path: Path) -> Path:
    """Si `path` ja existeix, retorna una variant amb ' (n)' que no col·lisioni."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    n = 1
    while True:
        candidate = path.with_name(f"{stem} ({n}){suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def to_mp3(src: Path, dst: Path) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("No s'ha trobat ffmpeg al PATH. Instal·la'l amb: brew install ffmpeg")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
           "-vn", "-c:a", "libmp3lame", "-b:a", "192k", str(dst)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg ha fallat sense missatge d'error.")


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


def transcribe(model, src: Path, language: str | None):
    """Transcriu `src` mostrant el percentatge a stderr; retorna (segments, info)."""
    segments_gen, info = model.transcribe(str(src), language=language, vad_filter=True, beam_size=5)
    segments = []
    for segment in segments_gen:
        segments.append(segment)
        if info.duration:
            log(f"\r  {min(segment.end / info.duration, 1.0) * 100:5.1f}%", end="")
    log("\r  100.0%")
    return segments, info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcriu àudio/vídeo a text en local (faster-whisper).")
    parser.add_argument("paths", nargs="+", help="Fitxers o carpetes d'àudio/vídeo")
    parser.add_argument("--model", default="medium", choices=WHISPER_MODELS)
    parser.add_argument("--lang", default="auto", choices=list(LANGUAGES))
    parser.add_argument("--format", default="txt", help="Formats separats per comes: txt,srt")
    parser.add_argument("--out", help="Carpeta de sortida (per defecte, la de cada fitxer)")
    parser.add_argument("--to-mp3", action="store_true", help="Desa també una còpia en mp3")
    args = parser.parse_args()
    args.formats = [f.strip() for f in args.format.split(",") if f.strip()]
    unknown = set(args.formats) - FORMATS
    if unknown or not args.formats:
        parser.error(f"Formats no vàlids: {', '.join(sorted(unknown)) or '(cap)'}. Opcions: txt, srt")
    return args


def main() -> int:
    args = parse_args()
    files = collect_files(args.paths)
    if not files:
        log("No s'ha trobat cap fitxer d'àudio/vídeo.")
        return 1

    out_dir = Path(args.out).expanduser() if args.out else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    # Import diferit: faster-whisper és pesat de carregar.
    from faster_whisper import WhisperModel

    log(f"Carregant model {args.model}... (el primer cop es descarrega a ~/.cache/huggingface)")
    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    failures = 0
    for src in files:
        dest_dir = out_dir or src.parent
        result: dict = {"src": str(src), "outputs": []}
        log(f"Transcrivint {src.name}")
        try:
            if args.to_mp3 and src.suffix.lower() != ".mp3":
                mp3 = resolve_collision(dest_dir / f"{src.stem}.mp3")
                to_mp3(src, mp3)
                result["outputs"].append(str(mp3))
            segments, info = transcribe(model, src, LANGUAGES[args.lang])
            for fmt in args.formats:
                dst = resolve_collision(dest_dir / f"{src.stem}.{fmt}")
                (write_txt if fmt == "txt" else write_srt)(segments, dst)
                result["outputs"].append(str(dst))
            result.update(status="ok", language=info.language, duration=round(info.duration, 1))
        except Exception as e:  # noqa: BLE001 - informem de qualsevol error per fitxer
            failures += 1
            result.update(status="error", error=str(e)[:500])
            log(f"  ERROR: {e}")
        print(json.dumps(result, ensure_ascii=False), flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
