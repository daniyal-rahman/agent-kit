# Agent kit

Makes your coding agents (Claude Code, Codex, and others that read an instruction
file) work for you like a good hire: they finish things, show proof, report
briefly, and stop making you repeat yourself.

The heart of it: your agent reads every past chat you've had with an AI that it
can find (Claude Code, Codex, ChatGPT or Claude.ai exports, other tools), finds the
friction that keeps coming up (what you had to correct, repeat or chase), spots
what you seem to know but never told it (you keep checking the same thing by
hand), and builds your setup against the worst of it. Then, with your OK, it
replays some of your past requests to show what the new setup would have fixed.

It has two parts:
- **What works for anyone**: a short instruction file (`core.md`) and a few skills
  for writing, reviews, research, design and improving work to a standard.
- **A setup that studies you**: your agent looks at your tools, your past agent
  chats and your work, measures where your time goes and what you keep having to
  correct, asks you a few questions, then builds your own instructions, your list
  of things you keep repeating, notes for your machines and projects, and
  (if you allow it) a voice library from your own writing.

## To start
Open Claude Code or Codex in this folder and say:

> Read SETUP.md in this folder and set me up

It works on its own for most of the time and messages you once, with what it
found and a few questions, each with a default. Plan on 1 to 3 hours of agent time
and about 10 minutes of yours. It uses a fair share of your plan's usage (a long
session plus some subagents); a voice library adds about 80 model calls.

## What it looks at
Your installed agent tools, your machine, every AI chat history it can find
(`~/.claude`, `~/.codex`, ChatGPT or Claude.ai export zips, other tools'
histories), your project folders, your existing instruction files, and only with
your say-so your mail or documents.

## What stays where
Everything it learns about you is written to `~/.agents/` on your machine and
nowhere else: not into this folder, not into git, not to any web service. It
links your agent tools' instruction files and skill folders to it, and it offers
(doesn't just do) a project instruction file for each of your main repos. Your
existing instruction files are backed up to `~/.agents/backup/` and their text is
kept. To update the kit later: `git pull` here, then `python3 install.py`.
