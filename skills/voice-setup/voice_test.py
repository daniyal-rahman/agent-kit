#!/usr/bin/env python3
"""Blind test: can a judge tell the owner's real writing from an AI draft?

Samples are text files in a library folder (private, never in git):
    kind: short-reply            <- header lines "key: value"
    relationship: collaborator
    to: first name only
    context: what the message answers / the situation
    ai_drafted: no
    ---
    body exactly as the owner sent it

Steps (each writes into RUN, so a run can be resumed or inspected):
    voice_test.py split   LIB RUN [--holdout 12]   pick held-out pieces, copy the rest to RUN/library
    voice_test.py briefs  RUN                       one call: neutral brief per held-out piece
    voice_test.py clean   RUN                       one call: fix typos/wrapping in held-out (not voice)
    voice_test.py gen     RUN COND [--guide F] [--library]   one draft per brief
    voice_test.py judge   RUN COND                  one call: blind pairs, judge picks the real one
    voice_test.py rate    RUN COND                  one call: each text alone, 0-100 chance it is real
                                                    (COND 'real' rates the originals: the baseline)
    voice_test.py report  RUN                       fooled-rate per condition (50% = perfect)

Calls `claude -p` with no user settings, so the owner's own instructions never
leak into the writer or the judge. Models: VT_WRITER (default sonnet),
VT_JUDGE (default opus). VT_OWNER sets the name used in the prompts.
"""
import argparse, concurrent.futures as cf, json, os, random, re, shutil, subprocess, sys, tempfile
from pathlib import Path

WRITER = os.environ.get("VT_WRITER", "sonnet")
JUDGE = os.environ.get("VT_JUDGE", "opus")
OWNER = os.environ.get("VT_OWNER", "the owner")


def parse(path):
    text = Path(path).read_text()
    head, _, body = text.partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["id"] = meta.get("id") or Path(path).stem
    return meta, body.strip()


def claude(prompt, model, system, tools="", add_dir=None, timeout=900):
    cmd = ["claude", "-p", "--model", model, "--system-prompt", system,
           "--no-session-persistence", "--setting-sources", "", "--tools", tools]
    if add_dir:
        cmd += ["--add-dir", str(add_dir), "--permission-mode", "bypassPermissions"]
    with tempfile.TemporaryDirectory() as cwd:  # empty cwd: no project files leak in
        r = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                           cwd=add_dir or cwd, timeout=timeout)
    if r.returncode:
        raise RuntimeError(r.stderr[-2000:])
    calls_log(model)
    return r.stdout.strip()


def calls_log(model):
    p = Path(os.environ.get("VT_RUN", ".")) / "calls.log"
    with open(p, "a") as f:
        f.write(model + "\n")


def json_from(text):
    m = re.search(r"\[.*\]|\{.*\}", text, re.S)
    return json.loads(m.group(0))


# ---------- split ----------
def cmd_split(a):
    run = Path(a.run); run.mkdir(parents=True, exist_ok=True); os.chmod(run, 0o700)
    items = [(p, *parse(p)) for p in sorted(Path(a.lib).glob("*.txt"))]
    human = [x for x in items if x[1].get("ai_drafted", "no").startswith("no")
             and len(x[2].split()) >= 12]
    rng = random.Random(a.seed)
    if a.ids:
        want = set(a.ids.split(","))
        held = [x for x in human if x[1]["id"] in want]
    else:  # spread across kinds
        bykind = {}
        for x in human:
            bykind.setdefault(x[1].get("kind", "other"), []).append(x)
        held, pools = [], [rng.sample(v, len(v)) for v in bykind.values()]
        while len(held) < a.holdout and any(pools):
            for p in pools:
                if p and len(held) < a.holdout:
                    held.append(p.pop())
    held_ids = {x[1]["id"] for x in held}
    lib = run / "library"; lib.mkdir(exist_ok=True)
    for p, meta, _ in items:
        if meta["id"] not in held_ids:
            shutil.copy(p, lib / p.name)
    (run / "holdout").mkdir(exist_ok=True)
    for p, _, _ in held:
        shutil.copy(p, run / "holdout" / p.name)
    write_index(lib)
    print(f"held out {len(held)}, library {len(items) - len(held)}")


def write_index(lib):
    rows = ["file\tkind\trelationship\tto\twords\tcontext"]
    for p in sorted(Path(lib).glob("*.txt")):
        m, b = parse(p)
        rows.append("\t".join([p.name, m.get("kind", ""), m.get("relationship", ""),
                               m.get("to", ""), str(len(b.split())), m.get("context", "")[:160]]))
    (Path(lib) / "INDEX.tsv").write_text("\n".join(rows) + "\n")


# ---------- briefs ----------
BRIEF_SYS = ("You turn real messages into neutral task briefs, the kind a person "
             "would give an assistant. Never copy the message's wording, phrasing, "
             "length, tone, greeting or sign-off. Give only facts: who it goes to and "
             "how the sender knows them, what it replies to, and every fact, date, "
             "number, name or request the message must contain.")


def cmd_briefs(a):
    run = Path(a.run)
    held = [parse(p) for p in sorted((run / "holdout").glob("*.txt"))]
    parts = [f"### {m['id']}\nRecipient: {m.get('to')} ({m.get('relationship')})\n"
             f"Situation: {m.get('context')}\nMessage:\n{b}" for m, b in held]
    prompt = ("For each message below write a brief of 2-5 sentences, starting "
              "'Write an email to ...'. Return JSON: {\"<id>\": \"<brief>\", ...}.\n\n"
              + "\n\n".join(parts))
    out = json_from(claude(prompt, WRITER, BRIEF_SYS))
    (run / "briefs.json").write_text(json.dumps(out, indent=1))
    print(f"{len(out)} briefs")


# ---------- gen ----------
GEN_SYS = ("You draft emails that {owner} will send under their own name. Output only "
           "the email itself, greeting through sign-off, no subject line and no commentary.")


def cmd_gen(a):
    run = Path(a.run)
    briefs = json.loads((run / "briefs.json").read_text())
    system = GEN_SYS.format(owner=OWNER)
    guide = Path(a.guide).read_text() if a.guide else ""
    lib = (run / "library").resolve()
    if guide:
        guide = guide.replace("~/.agents/voice/library", str(lib))
        system += "\n\nInstructions for writing as " + OWNER + ":\n" + guide
    out_dir = run / "drafts" / a.cond; out_dir.mkdir(parents=True, exist_ok=True)

    def one(item):
        pid, brief = item
        dest = out_dir / f"{pid}.txt"
        if dest.exists():
            return
        prompt = brief
        if a.library:
            prompt += ("\n\nThe library of " + OWNER + "'s real messages is " + str(lib)
                       + " (INDEX.tsv lists them). Use your tools to read samples, then "
                       "reply with only the final email.")
        text = claude(prompt, WRITER, system,
                      tools="Read,Glob,Grep" if a.library else "",
                      add_dir=lib if a.library else None)
        dest.write_text(text)

    with cf.ThreadPoolExecutor(6) as ex:
        list(ex.map(one, briefs.items()))
    print("drafts in", out_dir)


# ---------- clean ----------
CLEAN_SYS = ("You copy-edit minimally. Fix only misspellings, a clearly missing or "
             "doubled word, and stray spaces. Keep everything else exactly: wording, "
             "lowercase 'i', 'u', 'ur', run-on sentences, punctuation style, greeting, "
             "sign-off, line breaks.")


def unwrap(text):
    """Undo mail clients' hard wrap at ~72-78 columns, which no draft has."""
    out, prev = [], ""
    for line in text.splitlines():
        joinable = (out and out[-1] and line.strip() and 60 <= len(prev) <= 80
                    and not prev.rstrip().endswith((".", "!", "?", ":"))
                    and (len(line.split()) > 3 or line.strip()[:1].islower())
                    and not re.match(r"\s*([-*\d]+[.)]?\s|Eg:)", line))
        if joinable:
            out[-1] += " " + line.strip()
        else:
            out.append(line.rstrip())
        prev = line
    return "\n".join(out)


def cmd_clean(a):
    """Typos and mail wrapping are not voice: judge against a cleaned copy."""
    run = Path(a.run)
    held = [(p, *parse(p)) for p in sorted((run / "holdout").glob("*.txt"))]
    parts = [f"### {m['id']}\n{unwrap(b)}" for _, m, b in held]
    prompt = ("Copy-edit each message below. Return JSON: {\"<id>\": \"<text>\", ...}\n\n"
              + "\n\n".join(parts))
    out = json_from(claude(prompt, WRITER, CLEAN_SYS))
    d = run / "holdout_clean"; d.mkdir(exist_ok=True)
    for p, m, _ in held:
        head = p.read_text().partition("\n---\n")[0]
        (d / p.name).write_text(head + "\n---\n" + out[m["id"]].strip() + "\n")
    print(f"cleaned {len(out)} into {d}; read them before judging")


# ---------- judge ----------
JUDGE_SYS = ("You are an expert at telling one particular person's real writing from "
             "AI imitations. You are blunt and specific.")


def cmd_judge(a):
    run = Path(a.run)
    rng = random.Random(f"{a.cond}-{a.seed}")
    lib = sorted((run / "library").glob("*.txt"))
    refs = [parse(p) for p in lib if parse(p)[0].get("ai_drafted", "no").startswith("no")]
    refs = rng.sample(refs, min(a.refs, len(refs)))
    ref_txt = "\n\n".join(f"[reference {i+1}, to {m.get('relationship')}]\n{unwrap(b)}"
                          for i, (m, b) in enumerate(refs))
    pairs, key = [], {}
    hold = run / "holdout_clean" if (run / "holdout_clean").exists() else run / "holdout"
    for p in sorted(hold.glob("*.txt")):
        m, real = parse(p)
        d = run / "drafts" / a.cond / f"{m['id']}.txt"
        if not d.exists():
            continue
        fake = d.read_text().strip()
        real_first = rng.random() < 0.5
        A, B = (real, fake) if real_first else (fake, real)
        key[m["id"]] = "A" if real_first else "B"
        pairs.append(f"### pair {m['id']}\n--- A ---\n{A}\n--- B ---\n{B}")
    prompt = (f"Here are real emails written by one person:\n\n{ref_txt}\n\n"
              "Below are pairs. In each pair one email was really written and sent by "
              "this person; the other was written by an AI from a description of the "
              "same situation. Pairs are independent. For each pair pick the real one "
              "and say in one line what gave the other away.\n"
              "Return JSON: [{\"pair\": \"<id>\", \"real\": \"A\"|\"B\", "
              "\"confidence\": 1-3, \"tell\": \"...\"}]\n\n" + "\n\n".join(pairs))
    verdicts = json_from(claude(prompt, JUDGE, JUDGE_SYS))
    for v in verdicts:
        v["correct"] = v["real"] == key.get(v["pair"])
    out = run / "judgements"; out.mkdir(exist_ok=True)
    (out / f"{a.cond}-{a.seed}.json").write_text(json.dumps(verdicts, indent=1))
    fooled = sum(not v["correct"] for v in verdicts)
    print(f"{a.cond}: judge fooled {fooled}/{len(verdicts)}")


def cmd_rate(a):
    """Unpaired: rate each text alone, 0-100 chance the person wrote it.
    COND 'real' rates the cleaned held-out originals, as the baseline."""
    run = Path(a.run)
    rng = random.Random(f"rate-{a.seed}")
    lib = sorted((run / "library").glob("*.txt"))
    refs = [parse(p) for p in lib if parse(p)[0].get("ai_drafted", "no").startswith("no")]
    refs = random.Random(f"refs-{a.seed}").sample(refs, min(a.refs, len(refs)))
    ref_txt = "\n\n".join(f"[reference {i+1}, to {m.get('relationship')}]\n{unwrap(b)}"
                          for i, (m, b) in enumerate(refs))
    hold = run / "holdout_clean" if (run / "holdout_clean").exists() else run / "holdout"
    items = []
    for p in sorted(hold.glob("*.txt")):
        m, real = parse(p)
        if a.cond == "real":
            items.append((m["id"], real))
        else:
            d = run / "drafts" / a.cond / f"{m['id']}.txt"
            if d.exists():
                items.append((m["id"], d.read_text().strip()))
    rng.shuffle(items)
    body = "\n\n".join(f"### {i}\n{t}" for i, t in items)
    prompt = (f"Here are real emails written by one person:\n\n{ref_txt}\n\n"
              "Below are more emails. Any number of them, from none to all, may have been "
              "written by an AI imitating this person. For each, give the chance from 0 to "
              "100 that this person really wrote it, and what makes you doubt it.\n"
              "Return JSON: [{\"id\": \"<id>\", \"p_real\": 0-100, \"doubt\": \"...\"}]\n\n"
              + body)
    out = json_from(claude(prompt, JUDGE, JUDGE_SYS))
    d = run / "ratings"; d.mkdir(exist_ok=True)
    (d / f"{a.cond}-{a.seed}.json").write_text(json.dumps(out, indent=1))
    ps = [x["p_real"] for x in out]
    print(f"{a.cond}: mean p_real {sum(ps)/len(ps):.0f}, rated >=50: {sum(p >= 50 for p in ps)}/{len(ps)}")


def cmd_report(a):
    run = Path(a.run)
    rows = {}
    for f in sorted((run / "judgements").glob("*.json")):
        cond = f.stem.rsplit("-", 1)[0]
        v = json.loads(f.read_text())
        r = rows.setdefault(cond, [0, 0])
        r[0] += sum(not x["correct"] for x in v); r[1] += len(v)
    print("condition\tfooled\tjudged\tfooled%  (50% = indistinguishable)")
    for c, (f, n) in rows.items():
        print(f"{c}\t{f}\t{n}\t{100*f/n:.0f}%")
    if (run / "ratings").exists():
        print("\nunpaired rating (compare with 'real')\ncondition\tmean p_real\trated >=50")
        for f in sorted((run / "ratings").glob("*.json")):
            ps = [x["p_real"] for x in json.loads(f.read_text())]
            print(f"{f.stem.rsplit('-', 1)[0]}\t{sum(ps)/len(ps):.0f}\t{sum(p >= 50 for p in ps)}/{len(ps)}")
    log = run / "calls.log"
    if log.exists():
        print("model calls:", len(log.read_text().split()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("split"); s.add_argument("lib"); s.add_argument("run")
    s.add_argument("--holdout", type=int, default=12); s.add_argument("--seed", default="1")
    s.add_argument("--ids", help="comma-separated ids to hold out instead of picking")
    s = sp.add_parser("briefs"); s.add_argument("run")
    s = sp.add_parser("clean"); s.add_argument("run")
    s = sp.add_parser("gen"); s.add_argument("run"); s.add_argument("cond")
    s.add_argument("--guide"); s.add_argument("--library", action="store_true")
    s = sp.add_parser("judge"); s.add_argument("run"); s.add_argument("cond")
    s.add_argument("--refs", type=int, default=8); s.add_argument("--seed", default="1")
    s = sp.add_parser("rate"); s.add_argument("run"); s.add_argument("cond")
    s.add_argument("--refs", type=int, default=8); s.add_argument("--seed", default="1")
    s = sp.add_parser("report"); s.add_argument("run")
    a = ap.parse_args()
    os.environ["VT_RUN"] = a.run
    {"split": cmd_split, "briefs": cmd_briefs, "clean": cmd_clean, "gen": cmd_gen,
     "judge": cmd_judge, "rate": cmd_rate, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
