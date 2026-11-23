# Set up a person's agents

You are setting up the coding agents of the person who asked you to read this (the
owner). The goal: their agents work for them the way a good hire would, from day
one, without them having to repeat themselves. The kit gives you the parts that
hold for anyone (`core.md`, the skills). Your job is to study this person and build
the parts that are theirs, from their own chats, writing and machines.

Work like the rest of the kit says: find out before asking, rough version of
everything first, show proof. This can take a few hours. Most of it needs nothing
from the owner.

## Settings
Use these unless the owner or the person running you sets others:
- `KIT` = the folder this file is in.
- `LOOK` = where their history and instruction files are: `~` (their home
  folder). Every `~/...` path in steps 1 and 2 means `LOOK/...`. Facts about the
  machine itself (tools, OS, disks) come from the machine you're running on.
- `OUT` = where everything personal goes: `~/.agents`. Never write personal
  files into `KIT`; the kit is updated by `git pull`.
- `HOME_FOR_INSTALL` = the home the installer writes into: `~`. If it isn't `~`,
  pass `--home HOME_FOR_INSTALL` to every `install.py` command, `status` included.

Where you write: everything goes in `OUT`, plus the links the installer makes in
each agent tool's config folder. The one exception is a project instruction file
inside one of their repos (step 4), and only after they've seen it.

Keep progress in `OUT/setup-progress.md`: one line per step done, with what you
found and where you wrote it. If that file exists when you start, read it and
resume from the first step not done. Don't redo finished steps.

Privacy, for every step: chat history and mail name other people. Everything you
extract stays in `OUT` (`chmod 700`), is never committed, never pasted into a web
service, and goes only to models the owner already uses on this machine. Read
only; never delete, move or edit their history, mail or documents.

## 1. Look before asking (no questions yet)
Find out, and write each fact with its source into the progress file:
- **Agent tools**: which of `claude`, `codex`, `gemini`, `opencode`, `cursor-agent`,
  `aider` are on the PATH and their versions (`--version` only); whether they're
  signed in (a config folder with credentials; if unsure, one tiny test call) and
  which models they offer. Write "unknown" rather than guess.
- **Machine**: operating system, CPU/GPU, disk space; other machines it can reach
  (`~/.ssh/config` host names; don't log in anywhere yet). Keep apart a machine
  you inspected and one you only saw mentioned in chats.
- **Chat history**: `LOOK/.claude*/projects/`, `LOOK/.codex/sessions/`, Claude or
  ChatGPT export zips in Downloads (`conversations.json`), anything else you find.
  How many chats, from when to when.
- **Their work**: which folders hold it (git repos under home and common project
  folders), which are active (recent commits, recent chats), and what kind of work
  it is: code, research, data analysis, decks and docs, writing, ops. Read it from
  the repos and the chats, not from folder names alone.
- **Instructions they already have**: `~/.claude*/CLAUDE.md`, `~/.codex/AGENTS.md`,
  project `AGENTS.md`/`CLAUDE.md`, existing skills. These are theirs: keep them.
  The installer backs them up and carries their text over; never overwrite.
- **Connectors**: mail or document access the agents already have (MCP servers in
  the tools' config files, a mail export, a documents folder).

## 2. Profile their past work
Find where their attention goes and what keeps going wrong, before building
anything. Read it with these ideas: the owner's attention is the scarce thing; an
incident is an example of something the system should do for them; find why what
already exists didn't prevent it before adding anything; prefer a script, a check
or a skill with its own trigger over another sentence of instructions; count from
real records before believing a fix.

1. Run the counts (no model calls, a minute or two):
   `python3 KIT/profile/profile.py --root LOOK --out OUT/profile --owner <first name>`
   (add `--claude DIR --codex DIR` for history in other places; `--since` to limit
   it). The first name comes from `git config user.name`, their chats or their
   instruction files; `--owner` only helps drop messages that other agents wrote
   about them, so leave it out if you don't know it yet. Read `OUT/profile/profile.md`. It covers: what they send (new requests,
   corrections, "keep going / is it done"); their gaps between messages and free
   hour-long stretches; how long agents work per message and then wait for them;
   turns that ended in a permission question; how often a delivery's next reply is
   a correction, by model and by kind of work. These are text-pattern estimates:
   use them to choose where to look, and quote real messages as the evidence.
2. **Mine what they keep repeating.** `OUT/profile/corrections.tsv` has every
   message that looks like a correction, with the end of the agent's reply before
   it. The regex over-collects: read them and keep only those where the agent had
   skipped or got wrong something the owner expected. For each, read enough of the
   turn before to know what was skipped. Merge the same point across chats; count
   distinct chats; keep the owner's exact words (typos and all) and the date; take
   the latest word where they changed their mind. One project's standards go in
   that project's file, not the list. The rows are ordered round-robin across
   chats, so the first few hundred cover many chats; `source_file` locates the
   full turn. A long history: split the rows across subagents, each returning
   candidate items with quotes, then merge.
3. **Check why it wasn't prevented.** For each repeated item, look in the
   instructions they already had (step 1): was it written and still skipped (needs
   a trigger, a script or a check, not more words), or never written (a line in
   the right file may be enough)? With no earlier instructions to compare, say the
   cause is your hypothesis.
4. Write `OUT/profile/bottlenecks.md`, one screen: their **three biggest
   bottlenecks**, each with the number behind it, the cause, and what you'll build
   for it. Examples of the shape (not answers): "agents stop after 1 minute in half
   your turns and you reply 'continue' 14 times: core rule plus a project line on
   carrying work through verification"; "'did you test it' in 9 chats although
   your CLAUDE.md says to test: a check command in the project file instead of a
   sentence"; "you correct decks 3x as often as code: the writing and quality-loop
   skills, with a storyboard step".

## 3. One message to the owner
Send one message, one phone screen: what you found (tools, machines, kinds of
work, size of history), the three bottlenecks, then only the questions you could
not answer yourself, each with the default you'll use if they don't reply:
- Who uses their output (themselves, a team, clients, a supervisor)? (Default:
  what the chats show; otherwise themselves.)
- What is off limits: folders, accounts, people, kinds of data? (Default: nothing
  outside their home folder and repos; no mail, no accounts.)
- What may you read for the voice library and the repeat-list: sent mail, a
  documents folder, chats? (Default: chats only, and no voice library.)
- How they like to be reported to (default: the kit's rule, result first, about
  100 words, on a phone).
- A tag word for "you skipped things I already told you", which makes an agent go
  back through their instructions and chats and fix the misses. They pick it; it
  should be short and something they'd never type otherwise. (Default: none.)
- Which kind of work they want the agents to take more of. (Default: the current
  mix.)

Then stop and wait for the reply. If no one can reply (you're running headless) or
they say "use the defaults", continue with the defaults and list them in the
progress file.

## 4. Build: rough version of everything, then improve
Build all of these roughly first, then spend the remaining effort on whatever
serves the three bottlenecks most.
Prefer a check the agent runs when it matters (a test command, a script named in
the project file, a skill with its own trigger) over another sentence. Don't
install anything that watches or intercepts every chat (a hook at the end of each
turn, a scheduled nag) without the owner's explicit yes: one heavy user rejected
exactly that on sight. Propose it in the hand-over instead.
- `OUT/settings.json`: `{"owner": "<first name>", "tag": "<tag or empty>"}`.
- `OUT/me.md`: who they are and what they work on, who reads their output, what is
  off limits, how they want to be reported to, their machines (one line each), and
  which model to use for which kind of work given what they have (see
  `KIT/MODELS.md`; recommend, don't assume). Short: under 40 lines. Whatever only
  matters in one project goes in that project's file instead.
- `OUT/said-before.md`: the mined list from step 2, grouped by kind of work in the
  order an agent looks (any reply; decks and documents; screens; research and
  analysis; code and builds; long-running jobs; delegating). Each entry: one plain
  line of what to do, then their words in quotes, the date, and the number of
  chats. Most repeated first, at most about 15 per group.
- **Voice**: if they send things under their own name and allowed a source, follow
  `KIT/skills/voice-setup/SKILL.md`. Output goes in `OUT/voice/`.
- `OUT/machines/<hostname>.md` for each machine they use: what it's for, where
  things go, what's slow or fragile. The installer adds this machine's file to the
  universal file.
- **Projects**: an instruction file for their two or three most active projects:
  how to build, test and run it, who reads its output, and its standards from the
  mined list. Write it to `OUT/projects/<name>.md`; mark commands you didn't run
  as unverified. In the hand-over, offer to copy it into the repo as `AGENTS.md`
  (or merge it into the one there). Never commit in their repos.
- Install: `python3 KIT/install.py` (add `--home HOME_FOR_INSTALL` if it isn't
  `~`), then `python3 KIT/install.py status`. Rerun it after any change to `me.md`.

## 5. Prove it
Three levels; say which you reached. (a) `install.py status` shows every tool
linked. (b) A fresh agent loads the files. (c) A real past request gets a better
answer.
- Start a fresh agent in an empty folder, on each tool they use, with a task
  typical for this person (take one from `OUT/profile/requests.tsv`). Check from
  its output that it read the universal file (ask it what it knows about the
  owner), loaded the right skill for the task, and that its reply follows the
  reporting rule. If the tag is set, send it the tag and check the right skill
  fires. Fix what didn't load before you go on.
- Pick one real past request of theirs that got corrected. Run it again with the
  new setup and show the old reply, the correction they had to make, and the new
  reply, side by side. Say honestly if it isn't better. If you can't run the old
  request again (its files are gone), replay just the reply: give a fresh agent
  the chat up to that point and compare its answer with the corrected one.

## 6. Hand over
Send the owner one screen: what was built (paths), the three bottlenecks and what
now addresses each, the before/after, and what you couldn't do. Then how it grows:
- A correction they make twice goes in `said-before.md`: the tag skill adds it, or
  they say "add that to my said-before list" in any chat.
- A project lesson goes in that project's file, in one line with the reason.
- Add rules reluctantly. In one heavy user's audit, 9 of 13 corrections on decks
  were things their instructions already said; a rule that keeps being skipped
  needs a check, a script or a trigger, not more words. Delete lines a newer model no longer needs.
- Rerun `profile.py` in a month and compare the three numbers.
- To update the kit: `git pull` in `KIT`, then `python3 KIT/install.py`.
- With no tag word, they keep `said-before.md` current by asking any agent to add
  a line.
