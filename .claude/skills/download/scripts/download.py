#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yt-dlp"]
# ///
"""Descarrega vídeos públics de xarxes socials amb yt-dlp (sense iniciar sessió).

Ús:
    uv run download.py <url>... [--out DIR] [--audio-only]

Per defecte desa el vídeo en mp4 a ~/Downloads. `--audio-only` baixa només la
pista d'àudio (sense recodificar), pensat per transcriure-la després.

Només s'accepten les plataformes de `PLATFORMS`; per afegir-ne una, afegeix-hi
el domini. No es fan servir cookies ni sessions: només contingut públic.

Progrés a stderr; a stdout una línia JSON per URL amb el resultat.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Domini → nom de la plataforma. Els subdominis (www., m., mobile.) també valen.
PLATFORMS = {
    "instagram.com": "Instagram",
    "x.com": "X/Twitter",
    "twitter.com": "X/Twitter",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
}
# Paràmetres de query que cal conservar (la resta són de seguiment: psln, igsh, si...).
KEEP_PARAMS = {"v"}
LOGIN_HINTS = ("login", "log in", "sign in", "cookies", "authentication", "private")


def log(msg: str, end: str = "\n") -> None:
    print(msg, file=sys.stderr, end=end, flush=True)


def detect_platform(url: str) -> str | None:
    host = (urlsplit(url).hostname or "").lower()
    for domain, name in PLATFORMS.items():
        if host == domain or host.endswith("." + domain):
            return name
    return None


def clean_url(url: str) -> str:
    """Treu els paràmetres de seguiment i el fragment de l'URL."""
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k in KEEP_PARAMS])
    return urlunsplit((parts.scheme or "https", parts.netloc, parts.path, query, ""))


class StderrLogger:
    """Redirigeix els missatges de yt-dlp a stderr perquè stdout quedi net."""

    def debug(self, msg: str) -> None:
        if not msg.startswith("[debug]"):
            log(msg)

    def info(self, msg: str) -> None:
        log(msg)

    def warning(self, msg: str) -> None:
        log(f"AVÍS: {msg}")

    def error(self, msg: str) -> None:
        log(msg)


def progress_hook(d: dict) -> None:
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate")
        if total:
            log(f"\r  {d['downloaded_bytes'] / total * 100:5.1f}%", end="")
    elif d["status"] == "finished":
        log("\r  100.0%")


def download(url: str, out_dir: Path, audio_only: bool) -> dict:
    from yt_dlp import YoutubeDL

    opts = {
        "outtmpl": str(out_dir / "%(uploader).40s - %(title).80s [%(id)s].%(ext)s"),
        "format": "ba/b" if audio_only else "bv*+ba/b",
        "noplaylist": True,
        "quiet": True,
        "noprogress": True,
        "logger": StderrLogger(),
        "progress_hooks": [progress_hook],
    }
    if not audio_only:
        opts["merge_output_format"] = "mp4"
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    downloads = info.get("requested_downloads") or [{}]
    path = downloads[0].get("filepath") or ydl.prepare_filename(info)
    return {
        "path": path,
        "title": info.get("title"),
        "uploader": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Descarrega vídeos públics de xarxes socials (yt-dlp).")
    parser.add_argument("urls", nargs="+", help="Enllaços de vídeo")
    parser.add_argument("--out", default="~/Downloads", help="Carpeta de destí (per defecte ~/Downloads)")
    parser.add_argument("--audio-only", action="store_true", help="Només l'àudio, per transcriure'l")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for raw in args.urls:
        result: dict = {"url": raw}
        platform = detect_platform(raw)
        try:
            if platform is None:
                supported = ", ".join(sorted(set(PLATFORMS.values())))
                raise RuntimeError(f"Plataforma no suportada. Suportades: {supported}")
            url = clean_url(raw)
            result["platform"] = platform
            log(f"Descarregant de {platform}: {url}")
            result.update(download(url, out_dir, args.audio_only))
            result["status"] = "ok"
        except Exception as e:  # noqa: BLE001 - informem de qualsevol error per URL
            failures += 1
            msg = str(e)
            if any(hint in msg.lower() for hint in LOGIN_HINTS):
                msg = f"Aquest contingut demana iniciar sessió o és privat; només es poden baixar vídeos públics. ({msg})"
            result.update(status="error", error=msg[:500])
            log(f"  ERROR: {msg}")
        print(json.dumps(result, ensure_ascii=False), flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
