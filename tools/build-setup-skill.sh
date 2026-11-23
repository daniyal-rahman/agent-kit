#!/bin/sh
# skills/setup/SKILL.md is SETUP.md with a skill header. Run after editing SETUP.md; tools/check.sh fails if they differ.
cd "$(dirname "$0")/.."
{ printf -- '---\nname: setup\ndescription: set me up, set up my agents, agent kit setup, re-run setup, profile my agent use, rebuild my instructions, what do I keep repeating, bottlenecks in how I use agents.\n---\n\n'
  sed 's|^- `KIT` = the folder this file is in.$|- `KIT` = two folders up from this file, after following links (the agent-kit folder).|' SETUP.md; } > skills/setup/SKILL.md
