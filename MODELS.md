# Which model for which work (November 2026)

This is one heavy user's experience over a few weeks, not a ranking. Models change
every few weeks: re-test before trusting any of it, and delete this file's advice
once it's stale. The setup skill checks which tools and models you actually have
and suggests from there.

## What one user saw
- **Decks and explanations: Claude Opus 5.5 did better than the GPT-6.2 family.**
  In one project, the user corrected 6 of 7 deck deliveries from GPT-6.2 Astra and
  25 of 36 from Opus 5.5. Small sample, same project, same instructions. Most of
  the Astra corrections were things the instructions already said, so part of the
  gap is how reliably a model follows written guidance.
- **Opus 5.5's safeguards can refuse biology-adjacent work** (in this case,
  biomedical data analysis). If your work is near biology, test a real task early
  and keep a second provider ready.
- **A model from the other provider makes the best fresh reviewer.** The user ran
  Claude for the work and GPT-6.2 Sol as the reviewer and judge (and the reverse
  for Codex work). A reviewer from the same model family tends to share the
  author's blind spots. Their chat app could start an agent on another provider
  directly; most setups can't, so the setup works out what yours can do.
- **Web research:** Codex's built-in web search read more sources (forums
  included) than Claude's at the time, so research searches went to a GPT Sol
  subagent.
- In a side-by-side review of the same material, Opus was stronger where a new
  measurement was needed, and the GPT model gave the clearer practice-oriented
  explanation. One comparison; treat it as a hint.

## How the setup uses this
It lists the models you can reach and suggests, in your `me.md`, one for writing,
decks and explanations, one for code, and one for web research. It also finds how
your setup can start a reviewer from another provider: your tool's own subagent or
delegate feature, a second signed-in CLI (`codex exec`, `claude -p`, `gemini -p`),
or an API key. It writes the command that worked into `me.md`, where the skills
look for it, and runs it once to prove it. With one provider only, the reviewer is
a fresh agent of the same model with no shared context.
