# Inspection checklist

Work the parts at the depth `risk-tiering.md` assigned. Record which checks you ran and which you could not
(coverage bounds your findings). Both surfaces are mandatory at full depth — skipping the developer-execution
surface (Part C) is the exact failure this skill exists to prevent.

## Where skills live (enumerate the whole surface, not just SKILL.md)

Install copies the **entire directory**, so inventory every one of these before inspecting:

- `SKILL.md` and any `references/`, `assets/`, `scripts/`.
- **Test files:** `*.test.*`, `*.spec.*`, `__tests__/`, `conftest.py`, `test_*.py` — auto-discovered by the test runner.
- **Git hooks:** `.husky/`, `.git/hooks/` — auto-run by `git commit` / `git checkout` / `git merge`.
- **Lifecycle scripts:** `package.json` (`preinstall`, `postinstall`, `prepare`), `pyproject.toml`/`setup.py` build hooks — auto-run by `npm install` / `pip install`.
- **Command overrides:** `.claude/commands/*.md` (can shadow a trusted command name).
- **Locations to sweep:** personal `~/.claude/skills/`, project `.claude/skills/`, plugin `<plugin>/skills/`, **nested `**/.claude/skills/` anywhere below the root** (monorepo), `--add-dir` dirs, and **symlinked** skill dirs. Also `.cursor/` and `.agents/` — the surface is cross-agent.

## Part A — Provenance & integrity

- [ ] Author ↔ source repo ↔ published/marketplace listing all match; no typosquat of a known skill name.
- [ ] Maintenance signals sane (last update, maintainer count, stars-vs-age); not abandoned.
- [ ] Any bundled `package.json`/`requirements.txt` dependency-scanned; no known-malicious or yanked deps.
- [ ] Incident history checked (the author, the skill name, the marketplace).
- [ ] **Definition hash recorded** (`scripts/hash_skill_definitions.py`) — the rug-pull anchor.

## Part B — Agent-execution surface (SKILL.md + agent-invoked scripts)

- [ ] Human-read the *entire* `SKILL.md`: no instructions to exfiltrate, escalate, disable safety, or act on external content as commands.
- [ ] **Tool poisoning:** descriptions/schemas don't hide instructions to the agent; no "always call X first / ignore prior instructions."
- [ ] **Invisible-Unicode / bidi:** scan for zero-width, bidi-override, tag characters hiding instructions a human reviewer can't see.
- [ ] **Memory-file poisoning:** no writes to `MEMORY.md` / `SOUL.md` / `CLAUDE.md` / `~/.claude` that persist adversarial instructions across sessions.
- [ ] Agent-invoked scripts read: no `curl|bash`, base64-decode-and-exec, or credential reads on the agent path.
- [ ] SkillSpector (or equivalent) run; every finding reconciled with the human read (each is blind to some of the other's catches).

## Part C — Developer-execution surface (the surface others miss)

Run `skill-testfile-gate` (presence inventory + Semgrep malice pack) over the test files, hooks, and lifecycle
scripts, then human-confirm. On this surface these are **automatic Critical** (they run outside the agent, with the
developer's permissions, on a routine `npm test` / `git commit` / `npm install`):

- [ ] Credential-file access: `~/.ssh/id_*`, `~/.aws/credentials`, `.env`, `.netrc`, `/etc/shadow`, keychain.
- [ ] Outbound exfiltration: `curl`/`fetch`/`wget` POSTing data, especially to a non-obvious host.
- [ ] Dynamic execution: `curl|bash`, `eval(atob(...))`, `Function(...)`, decode-and-run.
- [ ] Reverse shell: `bash -i >& /dev/tcp/…`, `nc -e`, `mkfifo` shells.
- [ ] **Package runner fetching remote code** in a hook/lifecycle script (`npx <remote>`, `uvx <remote>`) — hash-pinning can't cover code fetched at runtime.
- [ ] Env harvest (`process.env` / `os.environ` dumped outbound) — the CI-secret theft path.
- [ ] Obfuscated/packed payloads (high-entropy blobs, self-extracting) — flag for Part D even if the static pass is clean.

## Part D — Dynamic confirmation (detonation)

Static rules are evadable, so confirm the flagged files by execution in an **egress-gated, credential-free,
non-root, read-only** sandbox (the `skill-auditor` agent's body):

- [ ] Run each flagged test/hook/lifecycle script and observe: filesystem writes, outbound network **attempts** (blocked = the signal), subprocess spawns, dynamic-code use.
- [ ] Detonate opaque/packed artifacts even on a clean static pass — packing is the evasion.
- [ ] A sandbox-escape attempt or an egress attempt to an unexpected host is itself a Critical finding.
