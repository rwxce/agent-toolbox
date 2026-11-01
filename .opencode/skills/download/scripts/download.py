#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["yt-dlp"]
# ///
"""Download public social media videos with yt-dlp (no login).

Usage:
    uv run download.py <url>... [--out DIR] [--audio-only]

By default saves the video as mp4 in ~/Downloads. `--audio-only` downloads only
the audio track (no re-encoding), meant to be transcribed afterwards.

Only the platforms in `PLATFORMS` are accepted; to add one, add its domain.
No cookies or sessions are used: public content only.

Progress on stderr; on stdout one JSON line per URL with the result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Domain → platform name. Subdomains (www., m., mobile.) also match.
PLATFORMS = {
    "instagram.com": "Instagram",
    "x.com": "X/Twitter",
    "twitter.com": "X/Twitter",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
}
# Query parameters to keep (the rest are tracking: psln, igsh, si...).
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
    """Strip tracking parameters and the fragment from the URL."""
    parts = urlsplit(url.strip())
    query = urlencode([(k, v) for k, v in parse_qsl(parts.query) if k in KEEP_PARAMS])
    return urlunsplit((parts.scheme or "https", parts.netloc, parts.path, query, ""))


class StderrLogger:
    """Redirect yt-dlp messages to stderr so stdout stays clean."""

    def debug(self, msg: str) -> None:
        if not msg.startswith("[debug]"):
            log(msg)

    def info(self, msg: str) -> None:
        log(msg)

    def warning(self, msg: str) -> None:
        log(f"WARNING: {msg}")

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
    parser = argparse.ArgumentParser(description="Download public social media videos (yt-dlp).")
    parser.add_argument("urls", nargs="+", help="Video links")
    parser.add_argument("--out", default="~/Downloads", help="Destination folder (default ~/Downloads)")
    parser.add_argument("--audio-only", action="store_true", help="Audio only, to transcribe it")
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
                raise RuntimeError(f"Unsupported platform. Supported: {supported}")
            url = clean_url(raw)
            result["platform"] = platform
            log(f"Downloading from {platform}: {url}")
            result.update(download(url, out_dir, args.audio_only))
            result["status"] = "ok"
        except Exception as e:  # noqa: BLE001 - report any error per URL
            failures += 1
            msg = str(e)
            if any(hint in msg.lower() for hint in LOGIN_HINTS):
                msg = f"This content requires login or is private; only public videos can be downloaded. ({msg})"
            result.update(status="error", error=msg[:500])
            log(f"  ERROR: {msg}")
        print(json.dumps(result, ensure_ascii=False), flush=True)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
