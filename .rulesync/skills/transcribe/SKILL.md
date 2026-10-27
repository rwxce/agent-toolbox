---
name: transcribe
description: >-
  Transcriu àudio o vídeo a text en local amb faster-whisper (sense API).
  Usa-la quan l'usuari demani transcriure, "passar a text", treure el text
  d'una reunió, nota de veu, podcast o vídeo, I TAMBÉ quan adjunti o enganxi
  directament un fitxer .m4a/.mp3/.mp4/.ogg/.opus/.wav/.webm/.mov sense cap
  altra instrucció (p. ex. un adjunt a .context/attachments/...).
targets: ["*"]
---

# Transcriure àudio/vídeo

Script: `scripts/transcribe.py` (dins d'aquesta carpeta de skill). S'executa amb
`uv run`, que instal·la les dependències automàticament (PEP 723).

Resultat esperat: **el text final al xat, sense deixar cap fitxer**, i l'àudio
original a la Paperera de macOS.

## Passos

1. **Resol el fitxer**: ruta que doni l'usuari o adjunt. Posa sempre les rutes
   entre cometes (sovint tenen espais i accents).
2. **Pregunta abans de transcriure**, totes les preguntes de cop (amb l'eina de
   preguntes si n'hi ha; si no, en un sol missatge). No tornis a preguntar el
   que l'usuari ja hagi dit.
   - **Idioma**: Català (`ca`) / Castellà (`es`) / Barreja català-castellà
     (`multi`) / Anglès (`en`).
   - **Qualitat**: `medium` (per defecte) / `large-v3` (més precís, més lent) /
     `small` (més ràpid).
   - **Context** (opcional): noms de persones, empreses, sigles, tema. Millora
     molt l'ortografia dels noms propis.
   - **Format de sortida**: Només transcripció (per defecte) / Transcripció +
     resum (amb diagrames i accions).
3. **Executa** (en segon pla si l'àudio és llarg; `medium` en CPU va
   aproximadament a temps real):

   ```bash
   uv run "<carpeta d'aquesta skill>/scripts/transcribe.py" "<fitxer>" \
     --print --trash-source --lang <ca|es|multi|en> --model <model> \
     [--prompt "<context>"]
   ```

   - `--print`: no escriu cap fitxer; el text arriba al JSON de stdout.
   - `--trash-source`: si ha anat bé, l'original va a la Paperera (i la carpeta
     de l'adjunt s'esborra si queda buida).
   - Si cal convertir el fitxer, l'script ho fa en una carpeta temporal que
     s'esborra sola.
   - El primer cop es descarrega el model a `~/.cache/huggingface`. Avisa'n.
4. **Llegeix el resultat**: una línia JSON per fitxer
   `{src, status, text, language, duration, trashed}` (o `error`). El progrés
   va a stderr.
5. **Respon** amb el **text sencer** al xat, en paràgrafs llegibles (no
   n'inventis ni en corregeixis el contingut), precedit de la durada. Digues que
   l'original és a la Paperera. Si hi ha `error`, explica'l: l'original no
   s'ha esborrat.
6. **Resum** (només si l'usuari l'ha demanat): després del text sencer, afegeix
   una secció `## Resum`, concisa però ben explicada, pensada per saber què cal
   fer. Basa't només en el que diu l'àudio; no inventis res.
   - **De què va**: 1-2 frases.
   - **Punts clau**: llista curta.
   - **Diagrama**: Mermaid `flowchart LR` de 3-6 caixes amb el flux, procés o
     decisions principals. Etiquetes en llenguatge planer (sense jerga), amb una
     nota curta amb `<br/>` només on importi. Si cal detall entre actors, un
     `sequenceDiagram` de 3-4 missatges com a màxim. Si no hi ha cap flux a
     dibuixar, una línia que ho expliqui en lloc d'un diagrama buit.
   - **Què cal fer**: llista ordenada d'accions concretes, amb responsable i
     termini si es mencionen.

## Ús manual (sense agent)

Sense `--print`, desa `.txt`/`.srt` al costat de l'original (`--format txt,srt`,
`--out <carpeta>`); `--to-mp3` desa també una còpia en mp3 (requereix `ffmpeg`).

## Errors habituals

- `uv` no trobat → `brew install uv`.
- `ffmpeg` no trobat → `brew install ffmpeg`.
