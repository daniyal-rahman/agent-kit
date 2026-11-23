---
name: research
description: research, look into, find out, has anyone built this, does this exist, competitors, alternatives, landscape, literature review, compare options, what's the best, state of the art, is it worth building, deep dive, every paper or tool on a topic.
---

# Research
Run research the way `quality-loop` describes. A good research answer:

- answers the question behind the request, and says what would change the answer
- separates what you opened yourself from what someone else reported
- says what it didn't find, where you looked, and why it would have shown up
  there. If something that probably exists isn't found, the search is the likely
  problem
- for a list, says how complete it is and how you know
- says where the owner's own idea falls short, not only where it's right

Search with whichever agent has the strongest web tool you can use (`MODELS.md`);
hand the searching to it as a subagent if you are on another one.

How a good researcher works through one question (invented case): the owner asks
"has anyone built something that watches a training run and tells you when it's
gone wrong? want to build one."

They write down the decision (build, adopt, or drop) and a guess: lots of people
train models and this isn't hard, so something probably exists, and an empty
first search would mean the search was wrong.

"Training run monitor" returns the well-known experiment trackers and roundup
articles that repeat each other. The trackers plot curves and leave the judging to
a person. That sameness says they are searching by a product name the builders may
never have used. Underneath, the thing is a watchdog on a number over time; someone
who needed it would have written a callback called "divergence check" or "NaN
guard". That points to code search for those words, the issue trackers of the big
training libraries, and the forums where people who train models complain.

That finds a small library whose README claims the feature. A README is cheap, so
they check: the detection code exists and has tests, several people committed over
two years, issues get answered, and two forum users describe real use, one
complaining about false alarms during warm-up.

The recommendation becomes "adopt it and fix the false alarms" instead of "build".
They stop looking, because a longer list wouldn't change that. The report opens
with the recommendation, then what the library lacks next to the owner's idea,
where they looked, and what they didn't do (they never ran it).
