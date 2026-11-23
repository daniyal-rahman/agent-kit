---
name: quality-loop
description: work that matters, quality, do it properly, review my work, fresh reviewer, review loop, second opinion, grade it, a report or deck or analysis others will act on, a feature the owner will rely on, before it goes to the owner, is this ready.
---

# Doing work that matters
Use as much of this as the task deserves: a quick lookup needs none, a report
others will act on needs all of it. The steps are proxies for a result that does
its job; if you can see it isn't good yet, following them doesn't make it done.

Before starting, write down what the owner will decide or do with the result,
what a finished version looks like, and the few things that separate a good one
from a passable one. Show the owner, and carry on if there's no reply.

Do the task to that standard. Then get a review from a fresh agent, started with
the reviewer command in `~/.agents/me.md` (a different model family when the owner
has one; otherwise the same model in a new session with no shared context).
Give it the owner's request in their exact words (not your summary), the work as
the owner will see it, and the part of `~/.agents/said-before.md` for this kind of
work. Leave out your reasoning and your opinion of the work.

Ask it, before it opens the work, to answer as the owner: the three or four things
they'd judge this on, and what would make them say no within five seconds. Then it
opens the work and gives the owner's first words on seeing it. Only then does it
read your own grading; where that missed what the owner would look at, that is its
first finding. (Asked this way, a fresh model predicted "a wall of small text I
have to scroll" for a dashboard the builder's own reviewers had passed at 4.5/5.)
It lists problems largest first. Large means it would change a decision or stop
the work doing its job. It checks by running and opening things; for a screen it
looks at the running thing, not the diff.

On substantial work use one reviewer per kind of failure: whether the claims hold,
whether the code behind the numbers is right, whether the audience can follow it.
One reviewer asked to cover everything gives the last one a paragraph.

Fix what it found, then repeat any review a fix could have undone. Stop when the
reviews find nothing large. If large problems remain after 4 rounds, stop and tell
the owner what still keeps it from being ready.

A review doesn't replace the owner's first look: a well-briefed reviewer has
missed most of what an owner later corrected. Where the purpose or the order of
the argument might be wrong, show the owner a one-screen outline early.

In the report, say which reviews ran, how the last one came out, and what you know
is still wrong. For a number to raise (speed, a score), see `hill-climb`.
