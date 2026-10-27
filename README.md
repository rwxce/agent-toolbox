# General

Eines, skills, comandes i subagents de propòsit general per a Claude Code, Codex, OpenCode i Cursor, amb una sola font a `.rulesync/` gestionada amb [rulesync](https://github.com/dyoshikawa/rulesync).

## Ús

```bash
npx rulesync generate          # regenera .claude/, .agents/, .opencode/, .cursor/, CLAUDE.md, AGENTS.md
npx rulesync generate --global # (opcional) instal·la-ho a ~/.claude, ~/.codex... per tenir-ho a tot arreu
```

Requisits: `node` (per `npx`), [`uv`](https://docs.astral.sh/uv/) (`brew install uv`) i, per a algunes eines, `ffmpeg`.

## Eines

| Eina | Com | Què fa |
| --- | --- | --- |
| `transcribe` | `/transcribe <fitxer>` o adjuntar l'àudio | Transcripció local d'àudio/vídeo amb faster-whisper (txt/srt) |

Ús directe sense agent:

```bash
uv run .rulesync/skills/transcribe/scripts/transcribe.py "reunio.m4a" --lang multi --prompt "Sara, Jordi" --print   # text a stdout, sense fitxers
uv run .rulesync/skills/transcribe/scripts/transcribe.py "reunio.m4a" --lang ca --format txt,srt     # desa .txt i .srt
```

## Afegir una eina nova

1. `.rulesync/skills/<nom>/SKILL.md` (frontmatter `name`, `description`, `targets: ["*"]`) i el codi a `scripts/`.
2. Opcional: `.rulesync/commands/<nom>.md` per tenir `/<nom>`.
3. `npx rulesync generate` i commit a `main`.
