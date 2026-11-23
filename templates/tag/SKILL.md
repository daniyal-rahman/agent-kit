---
name: already-told-you
description: Only when {{OWNER}}'s message is the tag itself, "{{TAG}}" (alone or nearly). Not for ordinary criticism of the work ("still bad", "did you test it"), which is feedback to act on directly, and not for routine checks before handing work over.
---

# "{{TAG}}"

{{OWNER}} sends this when what you just delivered skipped things they have
already told you, this project or other agents. They won't list them. Finding
them is the job, and so is fixing them before you answer.

Don't open with an apology, don't ask what was wrong, and don't promise anything
about next time. A reply that only says "I'll lead with the result from now on" is
the same miss again.

1. **Find what you skipped.** Read, in this order, until the list is clear:
   - {{OWNER}}'s own messages in this chat from the start, not your memory of
     them. If the chat was summarised, read the transcript.
   - This project's AGENTS.md or CLAUDE.md, then `~/.agents/AGENTS.md`.
   - `~/.agents/said-before.md`, the part for the kind of work you delivered.
   - The skills for that kind of work (`writing`, `ui-ux-design`, `quality-loop`,
     `research`). Load them; the name is not enough.
   - The last piece of this kind {{OWNER}} accepted in this project. That sets the
     look and the depth.
2. **Write the list:** each thing that was asked or standing, and its true state
   in what you delivered. Lines, not paragraphs.
3. **Fix every one now**, in this turn. Then look at the result the way {{OWNER}}
   will: open the rendered file, the screenshot, the running thing.
4. **Report** in the usual shape: one line naming what you had skipped, then the
   result with proof.
5. **Leave it findable.** If something you missed lived only in old chat, put it
   in the project's instruction file in one line with {{OWNER}}'s words and the
   date. If it would apply in other projects too, add it to
   `~/.agents/said-before.md`.

Why this exists: an agent once took over a long project chat and delivered a deck
with no figures, not in the audience's usual style, with no review, under a long
message. The owner had said all of it before, in other chats.
