---
name: hill-climb
description: hill climb, iterate until it's good, get it to a 9/10, score it, eval, benchmark, make it better, polish, optimize, improve quality, compare against competitors or references, keep going until, overnight improvement run. For open-ended UI, decks, writing, performance or organizing work.
---

# Hill climb
Turn "make it good" into a score, then raise it. The score is the easy part to get
wrong, so most of this is about keeping it honest.

## 1. Choose the score
- It comes from the owner's words and the reference, not from what is easy to
  check. With a reference (a product they named, a style reference), the judge
  sees yours and it side by side, unlabelled, and says which it would rather use
  and how far apart they are. Categories you pick yourself help find what to fix;
  they don't decide you are done.
- Correctness comes from things that run: tests, benchmarks, an agent that uses
  the UI. A judge scores only taste and clarity.
- Check the score against the real goal before climbing. Drop a metric that
  disagrees with what a person sees. Check the reference too: scoring against it
  copies its bugs.

## 2. Set up the judge
- A fresh agent every round, from the reviewer command in `~/.agents/me.md`. It
  gets the request, criteria, the artifact and fixed references; not your target,
  earlier scores or notes on what changed. Shared history makes judge and author
  drift into the same blind spot.
- Show the rendered thing, not your description of it.
- Ask which of two versions is better (both orders), or a 0 to 5 score. Fine
  1 to 10 steps are mostly noise.
- Score the start twice: with the reviewer, and with a fresh agent of your own
  model. Their gap is your noise.

## 3. Climb
- Work on the most important weak category first. Keep a change only if it beats
  the best so far by more than the noise.
- Keep a list of things that must not get worse (honest caveats, contrast,
  working interactions, size). A change that breaks one is rejected. On a tie,
  keep the smaller version.
- Each round, look at the best and worst versions yourself.
- After three rounds without gain, try one fresh rewrite and ask what's blocking;
  often it's the environment (tooling, compute, a missing check).

## 4. Stop
At the target on a fresh rescore by both, or when a fresh rewrite doesn't
help. Then cut what the score doesn't need. The owner decides where the top is.
Run long climbs on usage that would otherwise go unused (overnight). Report scores
by round, before and after, and what you cut.
