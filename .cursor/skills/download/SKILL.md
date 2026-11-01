---
name: download
description: Downloads public social media videos (Instagram, X/Twitter, YouTube) to ~/Downloads with yt-dlp, without logging in. Use it when the user pastes a social media link and wants the video ("download", "save the video", "descarrega", "baixa", "guarda el vídeo"). To transcribe a link, use the `transcribe` skill.
---
# Download social media videos

Script: `scripts/download.py` (inside this skill folder). Run it with `uv run`,
which installs `yt-dlp` automatically (PEP 723). No cookies or sessions: public
content only.

## Supported platforms

- Instagram (`instagram.com`: reels, posts)
- X/Twitter (`x.com`, `twitter.com`)
- YouTube (`youtube.com`, `youtu.be`, shorts)

## Steps

1. **Resolve the URL(s)** from the message. Always quote them. No need to clean
   them: the script strips tracking parameters (`?psln=`, `?igsh=`, `?si=`...).
2. **Run**:

   ```bash
   uv run "<this skill's folder>/scripts/download.py" "<url>" [--out <folder>]
   ```

   - By default it saves the video as mp4 in `~/Downloads`.
   - `--audio-only`: audio only, without re-encoding (this is what `transcribe`
     uses for a URL).
3. **Read the result**: one JSON line per URL
   `{url, platform, status, path, title, uploader, duration}` (or `error`).
   Progress goes to stderr.
4. **Reply** (in Catalan) with the platform, author, title and file path. If
   there is an `error`, explain it (unsupported platform, private or
   login-only content, post without video...).

## Adding a platform

1. Add the domain to `PLATFORMS` in `scripts/download.py` (`"tiktok.com": "TikTok"`).
2. Add it to the supported platforms list here and to the `description`.
3. Test it with a real link (yt-dlp supports most platforms).

## Common errors

- `uv` not found → `brew install uv`.
- `ffmpeg` not found (needed to merge video and audio) → `brew install ffmpeg`.
- A platform that used to work fails → yt-dlp updates often:
  `uv cache clean yt-dlp` and try again.
