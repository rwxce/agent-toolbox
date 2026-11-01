# agent-toolbox

General-purpose tools (transcription, social video download…) packaged as skills, commands and subagents for Claude Code, Codex, OpenCode and Cursor, with a single source in `.rulesync/` managed with [rulesync](https://github.com/dyoshikawa/rulesync).

## Usage

```bash
npx rulesync generate          # regenerates .claude/, .agents/, .opencode/, .cursor/, CLAUDE.md, AGENTS.md
npx rulesync generate --global # (optional) installs it into ~/.claude, ~/.codex... to have it everywhere
```

Requirements: `node` (for `npx`), [`uv`](https://docs.astral.sh/uv/) (`brew install uv`) and, for some tools, `ffmpeg`.

## Tools

| Tool | How | What it does |
| --- | --- | --- |
| `transcribe` | `/transcribe <file or link>` or attach the audio | Local audio/video transcription with faster-whisper (txt/srt), plus a summary with diagram and actions. Also accepts Instagram, X/Twitter and YouTube links (temporary audio download). |
| `download` | `/download <link>` or paste a link | Downloads public Instagram, X/Twitter and YouTube videos to `~/Downloads` with yt-dlp, no login. |

Direct use without an agent:

```bash
uv run .rulesync/skills/transcribe/scripts/transcribe.py "meeting.m4a" --lang multi --prompt "Sara, Jordi" --print   # text to stdout, no files
uv run .rulesync/skills/transcribe/scripts/transcribe.py "meeting.m4a" --lang ca --format txt,srt                   # saves .txt and .srt
uv run .rulesync/skills/download/scripts/download.py "https://www.youtube.com/watch?v=..."                           # mp4 in ~/Downloads
uv run .rulesync/skills/download/scripts/download.py "<url>" --audio-only --out /tmp/audio                           # audio only
```

## Adding a new tool

1. `.rulesync/skills/<name>/SKILL.md` (frontmatter `name`, `description`, `targets: ["*"]`) and the code in `scripts/`.
2. Optional: `.rulesync/commands/<name>.md` to get `/<name>`.
3. Add it to the tools table (and usage examples) in this README.
4. `npx rulesync generate` and commit to `main`.
