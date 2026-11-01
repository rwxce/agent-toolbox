# agent-toolbox

Single source of agent configuration (Claude Code, Codex, OpenCode, Cursor) generated with [rulesync](https://github.com/dyoshikawa/rulesync). General-purpose tools live here, packaged as skills, commands and subagents.

## Structure

- `.rulesync/rules/` — rules (this file generates `CLAUDE.md` / `AGENTS.md`).
- `.rulesync/skills/<name>/SKILL.md` + `scripts/` — each tool is a skill with its own code.
- `.rulesync/commands/<name>.md` — slash commands (`/<name>`).
- `.rulesync/subagents/` — subagents.
- Files in `.claude/`, `.codex/`, `.opencode/`, `.cursor/`, `.agents/`, `CLAUDE.md` and `AGENTS.md` are **generated**: do not edit them by hand. Edit `.rulesync/` and run `npx rulesync generate`.

## Conventions

- Language: everything in the repo (code, comments, docs, README, rules, skills, commands) is in English. Talk to the user in Catalan.
- Python scripts: a single file with inline dependencies (PEP 723), run with `uv run`. No manual venvs.
- Non-interactive scripts: CLI arguments, progress on stderr, machine-readable result (JSON) on stdout.
- When a new tool (skill and/or command) is added, update the tools table and usage examples in `README.md` in the same commit.
- If the user attaches an audio/video file with no other instruction, transcribe it with the `transcribe` skill: ask language, quality and context; give the text in the chat plus the summary (diagram and actions) without saving files; the original goes to the Trash.
- If the user pastes a social media link (Instagram, X/Twitter, YouTube) with no other instruction, ask whether they want to download it (`download` skill, to `~/Downloads`) or transcribe it (`transcribe` skill, temporary download).

## Git

- Work and commit **directly on `main`**: no branches or PRs. When a task is done, commit and `git push origin main`.
- After changing `.rulesync/`, run `npx rulesync generate` and include the generated files in the same commit.
