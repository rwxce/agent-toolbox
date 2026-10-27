---
root: true
targets: ["*"]
description: "Repo General: eines, skills, comandes i agents de propòsit general"
globs: ["**/*"]
---

# Repo General

Font única de configuració per a agents (Claude Code, Codex, OpenCode, Cursor) generada amb [rulesync](https://github.com/dyoshikawa/rulesync). Aquí viuen eines de propòsit general empaquetades com a skills, comandes i subagents.

## Estructura

- `.rulesync/rules/` — regles (aquest fitxer genera `CLAUDE.md` / `AGENTS.md`).
- `.rulesync/skills/<nom>/SKILL.md` + `scripts/` — cada eina és una skill amb el seu codi.
- `.rulesync/commands/<nom>.md` — slash commands (`/<nom>`).
- `.rulesync/subagents/` — subagents.
- Els fitxers a `.claude/`, `.codex/`, `.opencode/`, `.cursor/`, `CLAUDE.md`, `AGENTS.md` són **generats**: no els editis a mà. Edita `.rulesync/` i executa `npx rulesync generate`.

## Convencions

- Idioma: català (codi amb noms en anglès, comentaris i textos en català).
- Scripts Python: un sol fitxer amb dependències inline (PEP 723), executat amb `uv run`. Res de venv manual.
- Scripts no interactius: arguments CLI, progrés a stderr, resultat llegible per màquina (JSON) a stdout.
- Si l'usuari adjunta un fitxer d'àudio/vídeo sense cap altra instrucció, transcriu-lo amb la skill `transcribe`: pregunta idioma, qualitat i context; dona el text al xat sense desar fitxers; l'original va a la Paperera.

## Git

- Treballa i fes commit **directament a `main`**: res de branques ni PRs. En acabar una tasca, commit i `git push origin main`.
- Després de canviar `.rulesync/`, executa `npx rulesync generate` i inclou els fitxers generats al mateix commit.
