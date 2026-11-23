#!/usr/bin/env python3
"""Profile how someone works with their coding agents, from their own chat history.

Reads, all at once, any of:
  --root ~              finds Claude Code (~/.claude*/projects) and Codex (~/.codex/sessions) logs,
                        and ChatGPT or Claude export zips in ~/Downloads
  --claude DIR --codex DIR   those logs in other places
  --export FILE         a ChatGPT or Claude.ai data export: the .zip, or its conversations.json
  --messages FILE       anything else, converted first to plain JSON lines, one message per line:
                        {"chat": "id", "time": "2026-11-02T14:03:00Z" or epoch seconds,
                         "role": "user" or "assistant", "text": "...",
                         "model": "optional", "tool": "optional, e.g. cursor", "project": "optional"}
Nothing leaves the machine and no model is called: this is counting. The setup skill reads
the output and does the judging.

  python3 profile.py --root ~ --out ~/.agents/profile [--tz America/Los_Angeles] [--since 2026-08-01]

Writes into --out (chmod 700, it holds chat text):
  profile.md       the numbers, one section per question
  profile.json     the same numbers for scripts
  corrections.tsv  every message that looks like a correction, with the agent's text before it
  requests.tsv     the first message of every chat (what kind of work this is)
  messages.tsv     every message the person typed (session, time, model, project, text)
"""
import argparse, collections, datetime as dt, glob, json, os, re, statistics, sys
from zoneinfo import ZoneInfo

# Text that arrives as a "user" message but was not typed by the person.
NOT_HUMAN = re.compile(r"^\s*(<command-|<local-command|Caveat:|<teammate-message|<system-reminder>|\[Request interrupted"
    r"|Context handoff|\[T3 Code:|This session is being continued|<task-notification|<bash-|Base directory for this skill"
    r"|<user-prompt-submit-hook>|<environment_context>|<user_instructions>|# AGENTS\.md instructions|<turn_aborted>"
    r"|<subagent|Act as the [a-z-]+ sub-?agent|You are a (fresh|subagent|reviewer)|<permissions instructions>|\{\s*\")", re.I)
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>|\[Assistant quote\]\([^)]*\)", re.S)
AUTOMATED = re.compile(r"^\W*(\S+ )?(job result|background (command|task)|scheduled|delegated task|pointer from|digest|historical user"
    r"|[A-Z0-9 ]{4,} CONTEXT|[a-z]+ operating instructions|(claude|codex|agent) finished|task (complete|finished)|automated|cron|webhook)", re.I)

# Rough kinds of message. A regex is a first pass; the setup skill reads the corrections itself.
CORRECTION = re.compile(r"\b(did (u|you|ya)|didn'?t (u|you)|why (did|didn'?t|are|is|would|do)|i (told|said|asked)|already (told|said|asked)"
    r"|again\b|still (not|doesn|isn|broken|wrong|bad|sux|sucks)|forgot|not what i|that'?s not|wrong|how many times|stop\b|don'?t\b"
    r"|wtf|ffs|fuck|shit|sux|sucks|ugh|bruh|you were supposed|thats not|no[,.!]? (that|it|the|i)|remember|actually,|not my job"
    r"|wall of text|too long|too much text|sounds? (like )?ai|test(ed)? it|screenshot)", re.I)
CONTINUE = re.compile(r"^\s*(continue|keep going|go on|go ahead|proceed|carry on|next|resume|status\??|update\??|done\??|is it done|did it (finish|work)"
    r"|how'?s it going|any update|what'?s (the )?status|so\??|and\??|well\??|go|yes|yep|yeah|y|ok(ay)?|sure|do it|pls|please)\W*$", re.I)
ASKS_PERMISSION = re.compile(r"(want me to|should i|shall i|would you like me to|do you want me to|let me know if|if you'?d like|happy to)\b[^\n]*\??\s*$", re.I | re.S)
KINDS = [("decks and documents", r"\b(deck|slides?|pptx|presentation|report|write-?up|memo|doc(ument)?|pdf|email|draft|essay|paper)\b"),
         ("screens and UI", r"\b(ui|ux|screen|page|layout|css|design|button|frontend|mockup|app looks|dark mode|font)\b"),
         ("research", r"\b(research|look into|find out|compare|alternatives|literature|state of the art|has anyone|best way)\b"),
         ("data and analysis", r"\b(analy[sz]|dataset|plot|chart|figure|stats?|regression|model|train|eval|benchmark|notebook)\b"),
         ("ops and machines", r"\b(server|ssh|deploy|install|disk|cron|docker|gpu|slurm|service|network|backup|nas)\b")]
THEMES = {  # cheap cross-chat themes: what the person keeps saying, counted by distinct chat
    "didn't test / run it": r"did (u|you) (test|run|try|check)|test(ed)? it|does it (even )?work|not working|still broken",
    "no screenshots / can't see it": r"screenshot|show me|can'?t (see|open|find)|where is it|send (me )?(the )?(link|file)",
    "too long / unclear reply": r"too long|wall of text|too much text|tl;?dr|concise|simpler|plain english|confus|hard to follow|what does (this|that) mean",
    "sounds like AI / voice": r"sounds? (like )?(ai|chatgpt|gpt|robot)|not my voice|doesn'?t sound like me|em dash",
    "asked instead of doing": r"just do it|stop asking|why (are|do) (u|you) ask|don'?t ask|u can do|you can do (it|this)|do it urself|do it yourself",
    "stopped early / keep going": r"keep going|continue|didn'?t finish|not done|finish (it|the)|why did (u|you) stop|all of (it|them)",
    "repeat myself / remember": r"i (already )?(told|said|asked)|remember|again\b|how many times|repeat|go (thru|through) (the )?(chat|history)",
    "reinventing / check existing": r"reinvent|existing|already exists|library for|someone (has|already)|open.?source",
    "no review / quality": r"review|did (u|you) (check|look)|sloppy|quality|polish",
    "figures / visuals": r"figure|chart|plot|graph|visual|diagram",
    "lost the goal": r"zoom out|what are (we|u|you) (trying|doing)|the point|bigger picture|wh?at was the goal",
}

def iso(ts):
    return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))

def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") in ("text", "input_text", "output_text")]
        if any(isinstance(c, dict) and c.get("type") in ("tool_result", "function_call_output") for c in content):
            return ""
        return "\n".join(parts)
    return ""

def clean(t):
    t = REMINDER.sub("", t or "").strip()
    return "" if not t or NOT_HUMAN.search(t) else t

def read_claude(path):
    events, cwd, sid = [], None, os.path.basename(path)[:-6]
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("isSidechain"):
            continue
        cwd = d.get("cwd") or cwd
        ts, m = d.get("timestamp"), d.get("message") or {}
        if not ts:
            continue
        if d.get("type") == "user" and not d.get("isMeta"):
            t = clean(text_of(m.get("content")))
            if t:
                events.append(("human", iso(ts), t, None))
        elif d.get("type") == "assistant":
            t = text_of(m.get("content"))
            events.append(("agent", iso(ts), t, m.get("model")))
    return dict(tool="claude", session=sid, cwd=cwd, events=events, path=path)

def read_codex(path):
    events, cwd, model = [], None, None
    sid = os.path.basename(path)[:-6]
    sid = sid[-36:] if re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-", sid) else sid  # rollout-<date>-<uuid>
    for line in open(path, errors="replace"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        p, ts = d.get("payload") or {}, d.get("timestamp")
        if d.get("type") == "session_meta":
            cwd = p.get("cwd") or cwd
            if p.get("source") not in (None, "cli", "vscode", "exec", "mcp") and isinstance(p.get("source"), dict):
                return None  # a subagent spawned by another agent
        elif d.get("type") == "turn_context":
            model, cwd = p.get("model") or model, p.get("cwd") or cwd
        elif d.get("type") == "response_item" and p.get("type") == "message" and ts:
            if p.get("role") == "user":
                t = clean(text_of(p.get("content")))
                if t:
                    events.append(("human", iso(ts), t, None))
            elif p.get("role") == "assistant":
                events.append(("agent", iso(ts), text_of(p.get("content")), model))
    return dict(tool="codex", session=sid, cwd=cwd, events=events, path=path)

def when(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)) or re.fullmatch(r"\d+(\.\d+)?", str(v)):
        v = float(v)
        return dt.datetime.fromtimestamp(v / 1000 if v > 1e11 else v, dt.timezone.utc)
    t = iso(str(v))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)

def load_export(path):
    """ChatGPT or Claude.ai export (zip or conversations.json) -> sessions."""
    import zipfile
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            name = next((n for n in z.namelist() if n.endswith("conversations.json")), None)
            if not name:
                return []
            data = json.loads(z.read(name))
    else:
        data = json.load(open(path))
    out = []
    for c in data if isinstance(data, list) else []:
        events = []
        if "mapping" in c:  # ChatGPT: a tree of nodes; follow the branch that was kept
            tool, sid, node, chain = "chatgpt", c.get("conversation_id") or c.get("id"), c.get("current_node"), []
            while node and node in c["mapping"]:
                chain.append(c["mapping"][node]); node = c["mapping"][node].get("parent")
            for n in reversed(chain):
                m = n.get("message") or {}
                role, t = (m.get("author") or {}).get("role"), when(m.get("create_time"))
                parts = (m.get("content") or {}).get("parts") or []
                text = "\n".join(x for x in parts if isinstance(x, str)).strip()
                if t and text and role in ("user", "assistant"):
                    events.append(("human" if role == "user" else "agent", t, clean(text) if role == "user" else text,
                                   None if role == "user" else (m.get("metadata") or {}).get("model_slug")))
        elif "chat_messages" in c:  # Claude.ai
            tool, sid = "claude.ai", c.get("uuid")
            for m in c["chat_messages"]:
                text = m.get("text") or text_of(m.get("content"))
                t = when(m.get("created_at"))
                if t and text:
                    human = m.get("sender") == "human"
                    events.append(("human" if human else "agent", t, clean(text) if human else text, None))
        else:
            continue
        events = [e for e in events if e[2]]
        out.append(dict(tool=tool, session=str(sid), cwd=c.get("title") or c.get("name") or "web chat", events=events, path=path))
    return out

def load_messages(path):
    """The plain format: one JSON object per line (see the top of this file)."""
    chats = collections.OrderedDict()
    for n, line in enumerate(open(path, errors="replace"), 1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            t = when(d["time"])
        except (ValueError, KeyError) as e:
            print(f"{path}:{n}: skipped ({e})", file=sys.stderr)
            continue
        role = "human" if d.get("role") in ("user", "human") else "agent"
        text = clean(d.get("text", "")) if role == "human" else d.get("text", "")
        s = chats.setdefault(str(d.get("chat")), dict(tool=d.get("tool") or "other", session=str(d.get("chat")),
                                                       cwd=d.get("project"), events=[], path=path))
        if text:
            s["events"].append((role, t, text, d.get("model")))
    return list(chats.values())

def pct(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else None

def r1(x):
    return None if x is None else round(x, 1)

def kind_of(text):
    for name, rx in KINDS:
        if re.search(rx, text, re.I):
            return name
    return "code and builds"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", help="home folder to look in (finds .claude*/projects and .codex/sessions)")
    ap.add_argument("--claude", nargs="*", default=[]); ap.add_argument("--codex", nargs="*", default=[])
    ap.add_argument("--export", nargs="*", default=[]); ap.add_argument("--messages", nargs="*", default=[])
    ap.add_argument("--out", required=True); ap.add_argument("--tz", default=None); ap.add_argument("--since", default=None)
    ap.add_argument("--owner", default=None, help="the person's first name: messages that talk about them in the third person were written by an agent")
    a = ap.parse_args()
    if a.root:
        a.claude += [p for p in glob.glob(os.path.join(a.root, ".claude*/projects")) if os.path.isdir(p)]
        a.codex += [p for p in [os.path.join(a.root, ".codex/sessions"), os.path.join(a.root, ".codex/archived_sessions")] if os.path.isdir(p)]
        import zipfile
        for z in glob.glob(os.path.join(a.root, "Downloads", "*.zip")):
            try:
                if any(n.endswith("conversations.json") for n in zipfile.ZipFile(z).namelist()):
                    a.export.append(z)
            except (zipfile.BadZipFile, OSError):
                pass
    tz = ZoneInfo(a.tz) if a.tz else dt.datetime.now().astimezone().tzinfo
    files = [(read_claude, f) for d in a.claude for f in glob.glob(os.path.join(d, "**/*.jsonl"), recursive=True) if "/subagents/" not in f]
    files += [(read_codex, f) for d in a.codex for f in glob.glob(os.path.join(d, "**/*.jsonl"), recursive=True)]
    sessions = [s for s in (fn(f) for fn, f in files) if s]
    for f in a.export:
        sessions += load_export(f)
    for f in a.messages:
        sessions += load_messages(f)
    files += [(None, f) for f in a.export + a.messages]
    sessions = [s for s in sessions if any(e[0] == "human" for e in s["events"])]
    # Messages that share an opening with many others and run long were sent by a script, a scheduler or another agent.
    third = re.compile(r"\b" + re.escape(a.owner) + r"('s| (said|wants|asked|requested|just|is|has|will|would|can|needs|prefers|uses|decided|approved|told))\b", re.I) if a.owner else None
    opens = collections.Counter(e[2][:20] for s in sessions for e in s["events"] if e[0] == "human" and len(e[2]) > 300)
    auto = 0
    for s in sessions:
        keep = []
        for e in s["events"]:
            if e[0] == "human" and (AUTOMATED.search(e[2][:80]) or (len(e[2]) > 300 and opens[e[2][:20]] >= 5) or (third and third.search(e[2]))):
                auto += 1
                continue
            keep.append(e)
        s["events"] = keep
    sessions = [s for s in sessions if any(e[0] == "human" for e in s["events"])]
    since = dt.datetime.fromisoformat(a.since).replace(tzinfo=tz) if a.since else None
    os.makedirs(a.out, exist_ok=True); os.chmod(a.out, 0o700)

    msgs, turns, corr_rows, req_rows = [], [], [], []
    for s in sessions:
        ev = sorted(s["events"], key=lambda e: e[1])
        if since:
            ev = [e for e in ev if e[1] >= since]
        proj = (os.path.basename((s["cwd"] or "?").rstrip("/")) if s["tool"] in ("claude", "codex") else (s["cwd"] or s["tool"])) or "?"
        humans = [i for i, e in enumerate(ev) if e[0] == "human"]
        if not humans:
            continue
        req_rows.append((s["tool"], proj, ev[humans[0]][1].astimezone(tz).date().isoformat(), ev[humans[0]][2][:300]))
        work_kind = kind_of(" ".join(ev[i][2] for i in humans[:3]))
        for k, i in enumerate(humans):
            nxt = humans[k + 1] if k + 1 < len(humans) else len(ev)
            agent = [e for e in ev[i + 1:nxt] if e[0] == "agent"]
            last_text = next((e[2] for e in reversed(agent) if e[2].strip()), "")
            model = next((e[3] for e in reversed(agent) if e[3]), None)
            prev_agent = [e for e in ev[:i] if e[0] == "agent" and e[2].strip()]
            prev_text = prev_agent[-1][2] if prev_agent else ""
            prev_model = next((e[3] for e in reversed(ev[:i]) if e[0] == "agent" and e[3]), None)
            t, ts = ev[i][2], ev[i][1]
            kind = "correction" if (prev_text and len(t) < 800 and CORRECTION.search(t)) else "continue or approve" if CONTINUE.search(t) else "new request or info"
            msgs.append(dict(session=s["session"], tool=s["tool"], project=proj, ts=ts, text=t, kind=kind, prev_model=prev_model, work=work_kind))
            if kind == "correction":
                corr_rows.append((ts.astimezone(tz).strftime("%Y-%m-%d %H:%M"), s["tool"], prev_model or "?", proj, s["session"][:8],
                                  t[:1500].replace("\t", " ").replace("\n", " "), prev_text[-600:].replace("\t", " ").replace("\n", " "), s["path"]))
            if agent:
                end = agent[-1][1]
                reply = ev[nxt][1] if nxt < len(ev) else None
                turns.append(dict(session=s["session"], start=ts, end=end, minutes=(end - ts).total_seconds() / 60, model=model,
                                  work=work_kind, asked=bool(ASKS_PERMISSION.search(last_text[-300:])),
                                  wait=(reply - end).total_seconds() / 60 if reply else None,
                                  reply=ev[nxt][2] if reply else None))

    # 1. Attention: gaps between the person's messages across all chats.
    times = sorted(m["ts"] for m in msgs)
    gaps = [(b - a).total_seconds() / 60 for a, b in zip(times, times[1:])]
    on = [g for g in gaps if g < 240]
    days = sorted({t.astimezone(tz).date() for t in times})
    free60 = collections.Counter(b.astimezone(tz).date() for (a, b), g in zip(zip(times, times[1:]), gaps) if 60 <= g < 240)
    attention = dict(messages=len(msgs), automated_messages_left_out=auto, chats=len({m["session"] for m in msgs}), active_days=len(days),
                     messages_per_active_day=r1(len(msgs) / max(1, len(days))),
                     median_gap_min=r1(statistics.median(gaps)) if gaps else None,
                     share_of_on_time_in_gaps_under_15min=round(sum(g for g in on if g < 15) / max(1e-9, sum(on)), 2) if on else None,
                     free_hour_stretches_per_active_day=r1(sum(free60.values()) / max(1, len(days))),
                     chats_per_active_day=r1(statistics.mean(len({m["session"] for m in msgs if m["ts"].astimezone(tz).date() == d}) for d in days)) if days else None)
    # 2. What the person sends.
    kinds = collections.Counter(m["kind"] for m in msgs)
    # 3. How long agents work per message, and how long they then wait.
    mins = [t["minutes"] for t in turns]
    waits = [t["wait"] for t in turns if t["wait"] is not None and t["wait"] < 240]
    short = [t for t in turns if t["minutes"] < 2 and t["reply"] is not None]
    asked_then_yes = [t for t in turns if t["asked"] and t["reply"] and CONTINUE.search(t["reply"])]
    runs = dict(turns=len(turns), median_min=r1(pct(mins, .5)), p75_min=r1(pct(mins, .75)), p90_min=r1(pct(mins, .9)),
                share_under_2min=round(sum(m < 2 for m in mins) / max(1, len(mins)), 2),
                median_wait_for_person_min=r1(pct(waits, .5)), agent_hours_waiting_same_sitting=r1(sum(waits) / 60),
                turns_ending_in_a_permission_question=sum(t["asked"] for t in turns),
                of_those_answered_with_just_yes_or_go=len(asked_then_yes),
                short_turns_answered_with_continue=sum(1 for t in short if CONTINUE.search(t["reply"])))
    # 4. How often delivered work gets corrected, by model and by kind of work.
    def rate(key):
        c, n = collections.Counter(), collections.Counter()
        for t in turns:
            if t["reply"] is None:
                continue
            k = t[key] or "?"
            n[k] += 1
            c[k] += bool(len(t["reply"]) < 800 and CORRECTION.search(t["reply"]))
        return {k: dict(turns=n[k], corrected=c[k], share=round(c[k] / n[k], 2)) for k in sorted(n, key=lambda k: -n[k]) if n[k] >= 5}
    # 5. Repeated themes across chats.
    themes = {}
    for name, rx in THEMES.items():
        hit = [m for m in msgs if m["kind"] == "correction" and re.search(rx, m["text"], re.I)]
        if hit:
            first = min(hit, key=lambda m: m["ts"]); last = max(hit, key=lambda m: m["ts"])
            themes[name] = dict(chats=len({m["session"] for m in hit}), messages=len(hit), first=first["ts"].astimezone(tz).date().isoformat(),
                                last=last["ts"].astimezone(tz).date().isoformat(), example=last["text"][:160].replace("\n", " "))
    themes = dict(sorted(themes.items(), key=lambda kv: -kv[1]["chats"]))
    work = collections.Counter(m["work"] for m in msgs)
    projects = collections.Counter(m["project"] for m in msgs).most_common(10)
    tools = collections.Counter(m["tool"] for m in msgs)
    models = collections.Counter(t["model"] for t in turns if t["model"]).most_common(8)
    out = dict(window=[days[0].isoformat(), days[-1].isoformat()] if days else None, tools=dict(tools), models=dict(models),
               attention=attention, message_kinds=dict(kinds), agent_runs=runs, corrected_by_model=rate("model"),
               corrected_by_work=rate("work"), repeated_themes=themes, work_mix=dict(work.most_common()), top_projects=dict(projects))
    json.dump(out, open(os.path.join(a.out, "profile.json"), "w"), indent=1, default=str)

    with open(os.path.join(a.out, "corrections.tsv"), "w") as f:
        f.write("time\ttool\tmodel_before\tproject\tchat\twhat_they_said\tend_of_agent_reply_before\tsource_file\n")
        # Round-robin across chats, so reading the first N rows covers many chats rather than the busiest one.
        by_chat = collections.defaultdict(list)
        for r in sorted(corr_rows):
            by_chat[r[4]].append(r)
        queues, ordered = list(by_chat.values()), []
        while any(queues):
            for q in queues:
                if q:
                    ordered.append(q.pop(0))
        for r in ordered:
            f.write("\t".join(r) + "\n")
    with open(os.path.join(a.out, "requests.tsv"), "w") as f:
        f.write("tool\tproject\tdate\tfirst_message\n")
        for r in sorted(req_rows, key=lambda r: r[2]):
            f.write("\t".join(x.replace("\t", " ").replace("\n", " ") for x in r) + "\n")
    with open(os.path.join(a.out, "messages.tsv"), "w") as f:
        f.write("time\ttool\tproject\tchat\tkind\tmodel_before\ttext\n")
        for m in sorted(msgs, key=lambda m: m["ts"]):
            f.write("\t".join([m["ts"].astimezone(tz).strftime("%Y-%m-%d %H:%M"), m["tool"], m["project"], m["session"][:8], m["kind"],
                               m["prev_model"] or "?", m["text"][:500].replace("\t", " ").replace("\n", " ")]) + "\n")

    raw = len(files)
    L = [f"# Agent-use profile ({out['window'][0]} to {out['window'][1]})" if days else "# Agent-use profile (no messages found)", "",
         f"Read {raw} history files; {len(sessions)} chats had messages typed by the person ({len({m['session'] for m in msgs})} in the window). By tool: {dict(tools)}. Models seen: {dict(models)}.",
         "All counts below come from text patterns: treat them as estimates to check against corrections.tsv, not findings.", "",
         "## Where the person's attention goes",
         *[f"- {k.replace('_', ' ')}: {v}" for k, v in attention.items()], "",
         "## What they send", *[f"- {k}: {v} ({v / max(1, len(msgs)):.0%})" for k, v in kinds.most_common()], "",
         "## How long agents work per message, and then wait",
         *[f"- {k.replace('_', ' ')}: {v}" for k, v in runs.items()], "",
         "## How often the reply to a delivery is a correction",
         "By model:", *[f"- {k}: {v['corrected']}/{v['turns']} ({v['share']:.0%})" for k, v in out["corrected_by_model"].items()],
         "By kind of work:", *[f"- {k}: {v['corrected']}/{v['turns']} ({v['share']:.0%})" for k, v in out["corrected_by_work"].items()], "",
         "## Themes they keep correcting (regex first pass; read corrections.tsv for the real list)",
         *[f"- {k}: {v['chats']} chats, {v['first']} to {v['last']}. e.g. \"{v['example']}\"" for k, v in themes.items()], "",
         "## Kind of work (by the first messages of each chat)", *[f"- {k}: {v}" for k, v in work.most_common()], "",
         "## Busiest projects", *[f"- {k}: {v} messages" for k, v in projects], ""]
    open(os.path.join(a.out, "profile.md"), "w").write("\n".join(L))
    print("\n".join(L))

if __name__ == "__main__":
    main()
