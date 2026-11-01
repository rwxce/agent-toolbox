---
name: transcribe
description: 'Transcribes audio or video to text locally with faster-whisper (no API). Use it when the user asks to transcribe, "turn into text" ("transcriu", "passar a text"), get the text of a meeting, voice note, podcast or video, AND ALSO when they attach or paste an .m4a/.mp3/.mp4/.ogg/.opus/.wav/.webm/.mov file with no other instruction (e.g. an attachment in .context/attachments/...). It also transcribes social media links (Instagram, X/Twitter, YouTube): it downloads the audio to a temporary folder with the `download` skill and deletes it when done.'
---
# Transcribe audio/video

Script: `scripts/transcribe.py` (inside this skill folder). Run it with
`uv run`, which installs the dependencies automatically (PEP 723).

Expected outcome: **the final text in the chat, leaving no files behind**, and
the original audio in the macOS Trash (or, for a link, the temporary download
deleted).

## Steps

1. **Resolve the file**: path given by the user, or an attachment. Always quote
   paths (they often contain spaces and accents).
   - **If it is a social media link**, download only the audio to a temporary
     folder with the sibling `download` skill's script:

     ```bash
     tmp=$(mktemp -d)
     uv run "<skills folder>/download/scripts/download.py" "<url>" \
       --audio-only --out "$tmp"
     ```

     Use the JSON `path` as the file and offer the `uploader` and `title` as
     context. No `--trash-source`: when done (also on failure), delete the
     folder with `rm -rf "$tmp"`. If the download returns `error`, explain it
     and stop.
2. **Ask before transcribing**, all questions at once (with the question tool if
   available; otherwise in a single message), in Catalan. Don't re-ask what the
   user already said.
   - **Language**: Catalan (`ca`) / Spanish (`es`) / Catalan-Spanish mix
     (`multi`) / English (`en`).
   - **Quality**: `medium` (default) / `large-v3` (more accurate, slower) /
     `small` (faster).
   - **Context** (optional): names of people, companies, acronyms, topic.
     Greatly improves the spelling of proper nouns.
3. **Run** (in the background if the audio is long; `medium` on CPU runs at
   roughly real time):

   ```bash
   uv run "<this skill's folder>/scripts/transcribe.py" "<file>" \
     --print --trash-source --lang <ca|es|multi|en> --model <model> \
     [--prompt "<context>"]
   ```

   - `--print`: writes no file; the text arrives in the stdout JSON.
   - `--trash-source`: on success the original goes to the Trash (and the
     attachment folder is deleted if left empty).
   - If the file needs converting, the script does it in a temporary folder
     that is deleted automatically.
   - The first run downloads the model to `~/.cache/huggingface`. Warn the user.
4. **Read the result**: one JSON line per file
   `{src, status, text, language, duration, trashed}` (or `error`). Progress
   goes to stderr.
5. **Reply** with the **full text** in the chat, in readable paragraphs (don't
   invent or correct the content), preceded by the duration. Put the
   transcript **inside a code block** (close with ```text) so it can be copied
   in one click; nothing of the transcript outside the block. Say the original
   is in the Trash (or, for a link, that the temporary download was deleted).
   If there is an `error`, explain it: the original was not deleted.
6. **Summary** (always): after the full text, add a `## Resum` section, concise
   but well explained, meant to tell what needs to be done. Base it only on
   what the audio says; invent nothing.
   - **What it is about**: 1-2 sentences.
   - **Key points**: short list.
   - **Diagram**: Mermaid `flowchart LR` with 3-6 boxes showing the main flow,
     process or decisions. Plain-language labels (no jargon), with a short
     `<br/>` note only where it matters. If detail between actors is needed, a
     `sequenceDiagram` with at most 3-4 messages. If there is no flow to draw,
     one line saying so instead of an empty diagram.
   - **What to do**: ordered list of concrete actions, with owner and deadline
     if mentioned.

## Manual use (without an agent)

Without `--print`, it saves `.txt`/`.srt` next to the original
(`--format txt,srt`, `--out <folder>`); `--to-mp3` also saves an mp3 copy
(requires `ffmpeg`).

## Common errors

- `uv` not found → `brew install uv`.
- `ffmpeg` not found → `brew install ffmpeg`.
