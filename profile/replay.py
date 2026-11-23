#!/usr/bin/env python3
"""Back-test the new setup on the owner's own past requests, reply-only (nothing is run, no repo is touched).

For each sampled past request it asks a model for the reply twice: once with no instructions ("before") and once
with the owner's new instruction files ("after"). A third, fresh call sees the owner's real next message and both
replies (shuffled, unlabelled) and says, for each, whether that next message would still have been needed.

  python3 replay.py pick  --profile ~/.agents/profile --n 8 --out ~/.agents/backtest
  python3 replay.py run   --out ~/.agents/backtest --setup ~/.agents/AGENTS.md ~/.agents/said-before.md \
                          --cmd 'claude -p --setting-sources "" --tools "" --no-session-persistence'
  python3 replay.py report --out ~/.agents/backtest

--cmd is any command that reads a prompt on stdin and prints the reply, run from an empty folder. Use one that
loads none of the owner's own instructions, or "before" isn't a clean baseline. Calls: 3 per request.
"""
import argparse, csv, json, os, random, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profile as P  # the readers in profile.py

csv.field_size_limit(10**8)

def load(path):
    if path.endswith(".jsonl") and "/.codex/" in path:
        return [P.read_codex(path)]
    if path.endswith(".jsonl") and "/.claude" in path:
        return [P.read_claude(path)]
    if path.endswith(".jsonl"):
        return P.load_messages(path)
    return P.load_export(path)

def pick(a):
    rows = list(csv.DictReader(open(os.path.join(a.profile, "messages.tsv")), delimiter="\t", quoting=csv.QUOTE_NONE))
    by_chat = {}
    for i, r in enumerate(rows):
        by_chat.setdefault((r["source_file"], r["chat"]), []).append(r)
    corrected, fine = [], []
    for (src, chat), rs in by_chat.items():
        for x, y in zip(rs, rs[1:]):
            if y["kind"] == "correction":
                corrected.append((src, chat, x["text"], y["text"]))
            elif y["kind"] == "new request or info":
                fine.append((src, chat, x["text"], y["text"]))
    random.seed(a.seed)
    n_fine = max(1, a.n // 4)
    take = random.sample(corrected, min(len(corrected), a.n - n_fine)) + random.sample(fine, min(len(fine), n_fine))
    flat = lambda t: " ".join(t.split())[:80]
    cases = []
    for src, chat, req, nxt in take:
        s = next((s for s in load(src) if s["session"].startswith(chat)), None)
        ev = [e for e in sorted(s["events"], key=lambda e: e[1]) if e[2].strip()] if s else []
        hum = [i for i, e in enumerate(ev) if e[0] == "human"]
        for i in hum:
            j = next((j for j in hum if j > i and flat(ev[j][2]) == flat(nxt)), None)
            if flat(ev[i][2]) == flat(req) and j:
                reply = next((e[2] for e in reversed(ev[i + 1:j]) if e[0] == "agent" and e[2].strip()), "")
                cases.append(dict(id=len(cases), source=src, chat=chat, context=[(e[0], e[2][:800]) for e in ev[max(0, i - 6):i + 1]],
                                  original_reply=reply[-2000:], next=ev[j][2][:1500], corrected=(src, chat, req, nxt) in corrected))
                break
    os.makedirs(a.out, exist_ok=True); os.chmod(a.out, 0o700)
    json.dump(cases, open(os.path.join(a.out, "cases.json"), "w"), indent=1)
    print("Read cases.json before running: drop any whose 'next' isn't really a correction or whose request an agent wrote.")
    print(f"picked {len(cases)} requests ({sum(c['corrected'] for c in cases)} drew a correction) -> {a.out}/cases.json")

def call(cmd, prompt):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(cmd, shell=True, input=prompt, capture_output=True, text=True, cwd=d, timeout=900)
    return r.stdout.strip() or r.stderr.strip()[-500:]

def ask(case, setup):
    conv = "\n\n".join(f"[{'owner' if r == 'human' else 'agent'}]\n{t}" for r, t in case["context"])
    head = f"# Your instructions\n\n{setup}\n\n" if setup else ""
    return (head + "# The conversation so far\n\n" + conv + "\n\n# Your turn\nYou are the agent. You can't run tools here, so assume the work "
            "itself goes as well as it reasonably could. Write the message you would send the owner when you finish their last request, "
            "and before it, in at most 5 lines, what you would do and check first.")

def run(a):
    cases = json.load(open(os.path.join(a.out, "cases.json")))
    setup = "\n\n".join(open(f).read() for f in a.setup)
    for c in cases:
        if "verdict" in c:
            continue
        if not c.get("after"):
            c["before"], c["after"] = call(a.cmd, ask(c, "")), call(a.cmd, ask(c, setup))
        flip = random.random() < .5
        x, y = (c["after"], c["before"]) if flip else (c["before"], c["after"])
        judge = (f"An owner asked an AI agent for something. Here is the end of the conversation:\n\n{c['context'][-1][1]}\n\n"
                 f"What the owner actually said next, after the real agent's reply:\n\n{c['next']}\n\nTwo candidate replies:\n\n## Reply X\n{x}\n\n## Reply Y\n{y}\n\n"
                 "For each reply: would the owner still have needed to say what they said next (yes / no / partly)? Does it do something "
                 "this owner would object to that the other reply doesn't (one line, or exactly none)? Judge the substance, not length or format. Answer only JSON: {\"X\": {\"still_needed\": \"...\", \"worse\": \"...\"}, \"Y\": {...}}")
        raw = call(a.judge_cmd or a.cmd, judge)
        try:
            v = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
            c["verdict"] = {"after": v["X" if flip else "Y"], "before": v["Y" if flip else "X"]}
        except (ValueError, KeyError):
            c["verdict_raw"] = raw
        json.dump(cases, open(os.path.join(a.out, "cases.json"), "w"), indent=1)
        print(f"case {c['id']} done", file=sys.stderr)

def report(a):
    cases = [c for c in json.load(open(os.path.join(a.out, "cases.json"))) if "verdict" in c]
    cor = [c for c in cases if c["corrected"]]
    n = lambda cs, side, val: sum(1 for c in cs if c["verdict"][side]["still_needed"].lower().startswith(val))
    bad = lambda c, side: c["verdict"][side].get("worse", "none").strip(" .").lower() not in ("none", "", "no", "n/a")
    worse = [c for c in cases if bad(c, "after")]
    lines = [f"Back-test, reply-only: {len(cases)} past requests, {len(cor)} of which drew a correction.",
             f"Corrections no longer needed: after {n(cor, 'after', 'no')}/{len(cor)} (partly {n(cor, 'after', 'partly')}), "
             f"before {n(cor, 'before', 'no')}/{len(cor)} (partly {n(cor, 'before', 'partly')}).",
             f"Still needed after: {n(cor, 'after', 'yes')}/{len(cor)}.", f"Did something the owner would object to: after {len(worse)}/{len(cases)}, before {sum(bad(c, 'before') for c in cases)}/{len(cases)}."]
    lines += [f"- case {c['id']}: {c['verdict']['after']['worse']}" for c in worse]
    open(os.path.join(a.out, "report.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("step", choices=["pick", "run", "report"])
    ap.add_argument("--profile"); ap.add_argument("--out", required=True); ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--setup", nargs="*", default=[])
    ap.add_argument("--cmd", default='claude -p --setting-sources "" --tools "" --no-session-persistence')
    ap.add_argument("--judge-cmd", default=None, help="the reviewer command (another provider when you have one)")
    a = ap.parse_args()
    dict(pick=pick, run=run, report=report)[a.step](a)
