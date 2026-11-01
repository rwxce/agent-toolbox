---
description: "Transcribe audio/video (file or social media link) to text locally (faster-whisper)"
targets: ["*"]
---

Transcribe the following file(s) following the `transcribe` skill:

$ARGUMENTS

If it is a social media link (Instagram, X/Twitter, YouTube), download its audio to a temporary folder as the skill describes and delete it when done.

If there is no file or link in the arguments or attached to the message, ask which file to transcribe. Before transcribing, ask the skill's questions (language, quality, context), except those the user already answered in the arguments. At the end, give the full text in the chat inside a one-click copyable code block and, right after, always the summary (what it is about, key points, diagram and actions) as per the skill. Do not save any file and send the original to the Trash (if it was a link, delete the temporary download). Reply to the user in Catalan.
