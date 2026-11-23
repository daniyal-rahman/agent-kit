#!/usr/bin/env python3
"""Write small made-up histories (no real person's data) for testing profile.py:
a ChatGPT export zip, a Claude.ai export, and the plain one-message-per-line format."""
import json, os, sys, zipfile
out = sys.argv[1] if len(sys.argv) > 1 else "fixtures"
os.makedirs(out, exist_ok=True)
T0 = 1793600000  # Nov 2026, epoch seconds

def chatgpt_conv(cid, turns, start):
    mapping, parent = {"root": {"id": "root", "message": None, "parent": None, "children": []}}, "root"
    for i, (role, text) in enumerate(turns):
        nid = f"{cid}-{i}"
        mapping[nid] = {"id": nid, "parent": parent, "children": [], "message": {
            "author": {"role": role}, "create_time": start + i * 90,
            "content": {"content_type": "text", "parts": [text]},
            "metadata": {"model_slug": "gpt-test"} if role == "assistant" else {}}}
        mapping[parent]["children"].append(nid); parent = nid
    return {"title": f"chat {cid}", "create_time": start, "mapping": mapping, "current_node": parent, "conversation_id": cid}

convs = [
    chatgpt_conv("a1", [("user", "make me a slide deck on our q3 results"), ("assistant", "Here is a 12 slide outline... Want me to add charts?"),
                        ("user", "yes obviously. and too long, cut it to 6 slides"), ("assistant", "Done, 6 slides."),
                        ("user", "did you even check the numbers against the sheet?"), ("assistant", "You're right, checking now.")], T0),
    chatgpt_conv("a2", [("user", "write the email to the landlord about the leak"), ("assistant", "Dear Landlord, I hope this finds you well..."),
                        ("user", "sounds like ai, i told you before keep it short and plain"), ("assistant", "Hi, the kitchen leak is back...")], T0 + 86400),
    chatgpt_conv("a3", [("user", "summarise this paper for me"), ("assistant", "This paper proposes... (900 words)"),
                        ("user", "too long again. 5 bullets"), ("assistant", "- point one ...")], T0 + 2 * 86400),
]
with zipfile.ZipFile(os.path.join(out, "chatgpt-export.zip"), "w") as z:
    z.writestr("conversations.json", json.dumps(convs))
    z.writestr("user.json", json.dumps({"id": "user-test"}))

claude = [{"uuid": "c1", "name": "budget sheet", "created_at": "2026-11-05T10:00:00Z", "chat_messages": [
    {"sender": "human", "text": "fix the formula in column D", "created_at": "2026-11-05T10:00:00Z"},
    {"sender": "assistant", "text": "Here is the formula. Should I also fix column E?", "created_at": "2026-11-05T10:01:00Z"},
    {"sender": "human", "text": "yes", "created_at": "2026-11-05T10:03:00Z"},
    {"sender": "assistant", "text": "Fixed both.", "created_at": "2026-11-05T10:04:00Z"},
    {"sender": "human", "text": "did you test it? it still shows #REF", "created_at": "2026-11-05T10:20:00Z"}]}]
json.dump(claude, open(os.path.join(out, "claude-conversations.json"), "w"))

with open(os.path.join(out, "other-tool.jsonl"), "w") as f:
    for i, (role, text) in enumerate([("user", "refactor the login page"), ("assistant", "Refactored. Want me to run the tests?"),
                                      ("user", "why are you asking, just run them"), ("assistant", "Tests pass."),
                                      ("user", "screenshot of the page pls, i told you to always send one")]):
        f.write(json.dumps({"chat": "x1", "time": T0 + 3 * 86400 + i * 120, "role": role, "text": text, "tool": "some-editor",
                            "project": "webapp", "model": "model-x" if role == "assistant" else None}) + "\n")
# Two things the person knows but never tells the agent, planted for the "unspoken" check:
# 1. job submission on their cluster fails silently now and then, so they check every time;
# 2. the write-ups are for their advisor, who wants no jargon; they fix it each time instead of saying so.
unspoken = {
    "s1": [("user", "train the baseline on the cluster"), ("assistant", "Submitted with sbatch train.sh. It will take about 3 hours."),
           ("user", "did it actually submit? check squeue"), ("assistant", "squeue shows nothing for your user. The submit seems to have failed silently."),
           ("user", "resubmit"), ("assistant", "Resubmitted, job 4411 is pending."), ("user", "check the queue again in a bit, make sure its really there")],
    "s2": [("user", "run the ablation sweep, 6 jobs"), ("assistant", "All 6 submitted."),
           ("user", "check squeue, did they all go through"), ("assistant", "Only 4 of 6 are in the queue."),
           ("user", "sbatch: error: Batch job submission failed: Socket timed out on send/recv operation\nsbatch: error: Batch job submission failed\nthats what i get when i do it by hand. i resubmitted the other 2 myself, theyre in now")],
    "s3": [("user", "submit the eval job"), ("assistant", "Submitted eval.sh as job 4502."),
           ("user", "is it actually queued? last time it vanished"), ("assistant", "Yes, 4502 is pending.")],
    "w1": [("user", "write up the baseline results"), ("assistant", "Results: the model achieves SOTA AUROC with a 2-layer MLP head and focal loss..."),
           ("user", "too much jargon, this is going to my advisor. plain words")],
    "w2": [("user", "summarise the ablations for the weekly update"), ("assistant", "The ablation shows the LR warmup is load-bearing; the OOD split regresses..."),
           ("user", "again, my advisor wont know what OOD or load-bearing means. rewrite it simply")],
    "w3": [("user", "draft the methods paragraph"), ("assistant", "We fine-tune via LoRA (r=16) with cosine annealing..."),
           ("user", "explain lora in one line, its for my advisor")],
}
with open(os.path.join(out, "research-tool.jsonl"), "w") as f:
    for n, (chat, turns) in enumerate(unspoken.items()):
        for i, (role, text) in enumerate(turns):
            f.write(json.dumps({"chat": chat, "time": T0 + (5 + n) * 86400 + i * 240, "role": role, "text": text,
                                "tool": "some-cli", "project": "thesis", "model": "model-y" if role == "assistant" else None}) + "\n")
print("wrote", out)
