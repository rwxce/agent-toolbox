---
name: download
description: >-
  Descarrega vídeos públics de xarxes socials (Instagram, X/Twitter, YouTube)
  a ~/Downloads amb yt-dlp, sense iniciar sessió. Usa-la quan l'usuari enganxi
  un enllaç d'una xarxa social i vulgui el vídeo ("descarrega", "baixa",
  "guarda el vídeo"). Per transcriure un enllaç, usa la skill `transcribe`.
targets: ["*"]
---

# Descarregar vídeos de xarxes socials

Script: `scripts/download.py` (dins d'aquesta carpeta de skill). S'executa amb
`uv run`, que instal·la `yt-dlp` automàticament (PEP 723). Sense cookies ni
sessions: només contingut públic.

## Plataformes suportades

- Instagram (`instagram.com`: reels, posts)
- X/Twitter (`x.com`, `twitter.com`)
- YouTube (`youtube.com`, `youtu.be`, shorts)

## Passos

1. **Resol l'URL** (o URLs) del missatge. Posa-les sempre entre cometes. No
   cal netejar-les: l'script treu els paràmetres de seguiment (`?psln=`,
   `?igsh=`, `?si=`...).
2. **Executa**:

   ```bash
   uv run "<carpeta d'aquesta skill>/scripts/download.py" "<url>" [--out <carpeta>]
   ```

   - Per defecte desa el vídeo en mp4 a `~/Downloads`.
   - `--audio-only`: només l'àudio, sense recodificar (és el que fa servir
     `transcribe` amb un URL).
3. **Llegeix el resultat**: una línia JSON per URL
   `{url, platform, status, path, title, uploader, duration}` (o `error`). El
   progrés va a stderr.
4. **Respon** amb la plataforma, l'autor, el títol i la ruta del fitxer. Si hi
   ha `error`, explica'l (plataforma no suportada, contingut privat o que
   demana sessió, publicació sense vídeo...).

## Afegir una xarxa

1. Afegeix el domini a `PLATFORMS` de `scripts/download.py` (`"tiktok.com": "TikTok"`).
2. Afegeix-la a la llista de plataformes suportades d'aquí i a la `description`.
3. Prova-ho amb un enllaç real (yt-dlp suporta la majoria de xarxes).

## Errors habituals

- `uv` no trobat → `brew install uv`.
- `ffmpeg` no trobat (cal per ajuntar vídeo i àudio) → `brew install ffmpeg`.
- Falla una plataforma que abans anava → yt-dlp s'actualitza sovint:
  `uv cache clean yt-dlp` i torna-ho a provar.
