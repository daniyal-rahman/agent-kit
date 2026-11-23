---
name: voice-setup
description: Only for building or re-testing someone's voice library from their own writing (first-time voice setup, rebuild my voice, voice test). Not for drafting: a draft under the owner's name follows the voice file this setup produced.
---

# Voice setup
Gives agents the owner's voice for anything sent under their name, and measures
it. A description of a style ("short, no exclamation marks") barely moves a
model; the owner's real messages in front of it do. So the setup is a library
of real samples plus `candidate-voice.md`, which makes the writer copy the
closest sample. In the first test a judge rated drafts 22/100 on "did the
owner write this" with no guidance, 28 with a style description, and 55 with
this setup (the owner's real messages: 76).

## What stays private
The messages name other people. Keep the library, test runs and `edits.md` in
`~/.agents/voice/` (`chmod 700`). Never commit them, paste them into a web
service, or send them to any model except the one you run on. Only this skill,
`candidate-voice.md` and `voice_test.py` may be shared.

## 1. Find the owner's writing
Ask once where it lives, and look yourself: sent mail (a mail connector, or an
mbox/`.eml` export: sent folder only), a documents folder, AI chat history
(`~/.claude/projects`, `~/.codex/sessions`, ChatGPT or Claude export zips): the
owner's rejections of drafts there ("sounds like AI") say what to fix. Skip forms, forwards,
and anything an AI drafted: grep a distinctive phrase from each message in the
chat history. Mail from before chat assistants is the safest; childhood or
school writing is too old.

## 2. Build the library
One file per message in `~/.agents/voice/library/`: header lines `kind`,
`relationship`, `to` (first name), `context` (the situation, in your words),
`ai_drafted: no|likely|yes`, a line `---`, then the body as sent with quoted
replies removed. Aim for 40+ hand-typed, across kinds (short reply, scheduling,
cold email, thank-you, update, explanation) and audiences.

## 3. Test it
From this folder, `export VT_OWNER=<first name>`, `R=~/.agents/voice/run1`:
```
python3 voice_test.py split ~/.agents/voice/library $R --holdout 12
python3 voice_test.py briefs $R && python3 voice_test.py clean $R
python3 voice_test.py gen $R none
python3 voice_test.py gen $R samples --guide candidate-voice.md --library
python3 voice_test.py rate $R real   # then: rate $R none, rate $R samples
python3 voice_test.py judge $R samples
python3 voice_test.py report $R
```
Check the briefs don't copy the owner's wording, and the cleaned originals
(`clean` fixes typos and mail line wraps, which aren't voice). Climb on `rate`
(each text alone) against `real`; side-by-side `judge` is nearly always won by
a strong judge. Fix the most common doubt, rerun under a new name, stop after
three rounds or when it stops moving. About 80 model calls.

## 4. Hand over
Copy `candidate-voice.md` to where the owner's agents read instructions. Give
the owner the scores side by side and six real-vs-draft pairs to judge blind,
answers at the bottom: they are the real judge.
