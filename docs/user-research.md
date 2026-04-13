# PromptIQ User Research Notes

Date: 2026-04-13

Goal: pressure-test PromptIQ against how serious AI CLI users actually work, and avoid building a scoring toy that sounds smart but does not change behavior.

## What We Looked For

- how advanced users structure AI coding sessions
- where people complain about context bloat and vague prompting
- what makes installable AI tools feel trustworthy
- how nearby open source tools position themselves

## Strong Signals

### 1. Specific constraints beat broad ambition

Across Claude Code discussions, the strongest usage patterns were not "write a brilliant prompt once." They were:

- narrow the task
- state constraints early
- define what a successful answer must contain
- correct drift quickly

Implication for PromptIQ:

- reward output constraints and corrective follow-ups heavily
- keep punishing vague "make it great" style prompting

### 2. Context hygiene matters as much as raw prompt quality

Advanced users repeatedly talk about using persistent files, scoped task prompts, and lighter sessions to avoid context collapse. Long sessions with weak structure are widely seen as noisy rather than expert.

Implication for PromptIQ:

- keep session quality separate from session length
- explain why verbose but weakly steered sessions should not score well
- reinforce scoped context as a first-class habit

### 3. Verification planning is a major separator

In serious AI coding work, stronger users do not stop at "give me the fix." They ask how the fix will be checked: tests, logs, repro steps, comparisons, or explicit falsification conditions.

Implication for PromptIQ:

- do not treat tool usage as a full substitute for verification thinking
- reward sessions that define how success will be proven
- make missing verification paths visible in `Why It Is Not Higher`

### 4. Users want reusable workflow habits, not command sprawl

Community feedback around AI coding workflows shows a preference for small numbers of reusable patterns over giant command catalogs or oversized instruction files.

Implication for PromptIQ:

- keep the product surface area tight
- make `/score` excellent before adding more commands
- make the README explain behavior quickly instead of burying users in options

### 5. Install trust is a real UX problem

People regularly hit the "I installed it, but is it actually wired up?" problem with CLI-first tools. That uncertainty is extra damaging for a tool that is supposed to judge rigor.

Implication for PromptIQ:

- ship a simple `doctor` self-check
- print a verification command after install
- make file paths and local state obvious

### 6. The adjacent market is already crowded with prompt eval tools

Projects like Promptfoo already cover prompt regression testing, eval datasets, and model comparisons very well. That means PromptIQ should stay differentiated.

Implication for PromptIQ:

- position PromptIQ as a strict session coach
- do not drift into generic prompt testing language
- focus on human steering quality inside real AI CLI sessions

## Product Decisions Driven By This Research

- add a `doctor` command for install verification and local-state visibility
- rewrite the README around real user jobs-to-be-done
- keep the "session review" claim narrow and credible
- make verification planning part of high-score behavior
- favor calibration, fixtures, and contributor guidance over shallow feature expansion

## Sources Consulted

- [Anthropic: Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Reddit `r/ClaudeAI` search: Claude Code tips](https://www.reddit.com/r/ClaudeAI/search/?q=Claude%20Code%20tips&restrict_sr=1&sort=relevance)
- [Hacker News search: Claude Code workflow discussions](https://hn.algolia.com/?q=%22Claude%20Code%22%20workflow)
- [V2EX discussion search: AI coding workflow habits](https://www.google.com/search?q=site%3Av2ex.com+AI+%E7%BC%96%E7%A8%8B+agent+%E6%8F%90%E7%A4%BA%E8%AF%8D+%E8%BE%93%E5%87%BA+%E6%A0%BC%E5%BC%8F)
- [Promptfoo repository](https://github.com/promptfoo/promptfoo)
