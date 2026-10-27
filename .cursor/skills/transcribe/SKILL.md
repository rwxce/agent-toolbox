---
name: transcribe
description: Transcriu àudio o vídeo a text en local amb faster-whisper (sense API). Usa-la quan l'usuari demani transcriure, "passar a text", treure el text d'una reunió, nota de veu, podcast o vídeo, I TAMBÉ quan adjunti o enganxi directament un fitxer .m4a/.mp3/.mp4/.ogg/.opus/.wav/.webm/.mov sense cap altra instrucció (p. ex. un adjunt a .context/attachments/...).
---
# Transcriure àudio/vídeo

Script: `scripts/transcribe.py` (dins d'aquesta carpeta de skill). S'executa amb
`uv run`, que instal·la les dependències automàticament (PEP 723). No cal
convertir a mp3: faster-whisper llegeix m4a/mp4/ogg/wav... directament.

## Passos

1. **Resol els fitxers**: rutes que doni l'usuari o adjunts. Posa sempre les
   rutes entre cometes (sovint tenen espais i accents). Si diu "l'últim àudio
   de Downloads", busca el més recent amb `ls -t`.
2. **Executa** (en segon pla si l'àudio dura més de ~5 min; el model `medium`
   va aproximadament a temps real o més ràpid en CPU):

   ```bash
   uv run "<carpeta d'aquesta skill>/scripts/transcribe.py" "<fitxer>" [més fitxers o carpetes] \
     [--lang auto|ca|es|en] [--model tiny|base|small|medium|large-v3] \
     [--format txt,srt] [--out <carpeta>] [--to-mp3]
   ```

   - Per defecte: `--model medium --lang auto --format txt`, sortida al costat
     de l'original (`nom.txt`; si ja existeix, `nom (1).txt`).
   - Si l'usuari indica l'idioma, passa `--lang`; millora la precisió.
   - `--model large-v3` si demana màxima qualitat; `small` si té pressa.
   - El primer cop es descarrega el model (~1.5 GB per `medium`) a
     `~/.cache/huggingface`. Avisa'n.
   - Si l'usuari vol l'mp3, afegeix `--to-mp3` (requereix `ffmpeg`).
3. **Llegeix el resultat**: cada línia de stdout és un JSON
   `{src, outputs, status, language, duration}` (o `error`). El progrés va a
   stderr.
4. **Informa**: ruta(es) de sortida, idioma detectat i durada, i un fragment
   inicial del text (no l'enganxis sencer). Ofereix fer-ne un resum, actes o
   llista de tasques si té sentit.

## Errors habituals

- `uv` no trobat → `brew install uv`.
- `ffmpeg` no trobat (només amb `--to-mp3`) → `brew install ffmpeg`.
