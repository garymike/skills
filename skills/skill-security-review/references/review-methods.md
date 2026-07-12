# Review methods — how to ingest a skill, and the fallback when a tool is missing

Pick the mode(s) your access allows. They are complementary — each is blind to what the others catch — so run as
many as you can and reconcile them. A repo-vs-published divergence is itself a finding.

## Modes

| Mode | You have… | Drives | How |
|---|---|---|---|
| **Source review** | A repo/marketplace link | Parts A, B, C | Clone at a **pinned commit** (record the SHA). Enumerate the whole bundle (checklist location list). Human-read `SKILL.md`; run both scanners over source. |
| **Local review** | An installed copy on disk | Parts A–C | Inspect the installed directory as-shipped — catches published-vs-repo divergence and post-install file state. |
| **Sandbox review** | The ability to run it | Part D | Detonate flagged files in the egress-gated, credential-free sandbox and observe. The only mode that confirms evadable static findings. |

Given only a link, **do not install to review** — clone and read first; install (which copies the whole directory
and may fire lifecycle scripts) is itself a developer-execution event.

## Scanners and their manual fallback

Record which you actually ran; a missing tool becomes a manual step, not a skipped check.

| Tool | Covers | If unavailable, do manually |
|---|---|---|
| **`skill-testfile-gate`** (security-workflows) | Developer-execution surface: presence inventory + Semgrep malice pack over tests/hooks/lifecycle | `grep -r` the auto-run files for the Part C patterns (credential paths, `curl\|bash`, `eval(atob`, `/dev/tcp/`, `process.env` egress, `npx`/`uvx` in hooks); inventory invisible-Unicode. |
| **SkillSpector** (NVIDIA) | Agent-execution surface: `SKILL.md`/script prompt-injection, tool poisoning | Human-read the full `SKILL.md`; check descriptions/schemas for hidden instructions. |
| **Dependency/secret scan** (osv-scanner, trufflehog, betterleaks) | Bundled deps + hardcoded secrets | `grep` for key-shaped strings; check `package.json`/`requirements.txt` against known-bad. |
| **Sandbox** (skill-auditor compose) | Dynamic behavior | State "not detonated" as a coverage limitation; the verdict cannot be CLEAR on an un-observed developer-execution surface. |

## Reconcile, don't average

If SkillSpector clears the agent surface but the gate flags a `.husky/pre-commit`, the skill is **flagged** — the
surfaces are independent, and the developer-execution finding stands on its own. This is the whole reason both
surfaces are inspected.
