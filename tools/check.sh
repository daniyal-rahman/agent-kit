#!/bin/sh
# Checks before a commit: the setup skill matches SETUP.md, skills stay short, nothing personal leaked in.
cd "$(dirname "$0")/.."; fail=0
tmp=$(mktemp); cp skills/setup/SKILL.md "$tmp"; sh tools/build-setup-skill.sh
cmp -s "$tmp" skills/setup/SKILL.md || { echo "setup skill was out of date (rebuilt it)"; fail=1; }; rm -f "$tmp"
for f in skills/*/SKILL.md templates/*/SKILL.md; do
  case $f in skills/setup/*|skills/voice-setup/*) continue;; esac
  n=$(wc -l < "$f"); [ "$n" -le 50 ] || { echo "$f has $n lines (limit 50)"; fail=1; }
done
python3 -m py_compile install.py profile/profile.py skills/voice-setup/voice_test.py || fail=1
[ "$fail" = 0 ] && echo ok
exit $fail
