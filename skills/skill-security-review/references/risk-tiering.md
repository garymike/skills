# Risk tiering — assessment depth and automatic disqualifiers

Set depth in Step 1 by what the skill *ships and touches*. The developer-execution surface drives the tier: a
skill that bundles auto-run files is never a fast pass.

## Depth tiers

| Tier | The skill is… | Depth |
|---|---|---|
| **Fast pass** | Docs/instructions only — no `scripts/`, no test files, no hooks, no lifecycle scripts, no memory writes | Part A + a human read of `SKILL.md` (Part B). State that no developer-execution surface was present. |
| **Standard** | Ships agent-invoked scripts OR a small test/asset set, no hooks/lifecycle scripts | Parts A–C. Run both scanners. |
| **Full** | Ships **git hooks, npm/pip lifecycle scripts, or test files**, writes agent memory, or requests broad reach | Parts A–D, including **sandbox detonation** of flagged files. |

When unsure, tier **up**. The cost of over-inspecting a benign skill is minutes; the cost of a fast-passed
`postinstall` is the developer's SSH key.

## Automatic disqualifiers (a finding, regardless of tier)

Any of these is a Critical and caps the verdict at **block / do-not-install** until resolved:

- A developer-execution-surface Critical (credential access, exfil, dynamic-exec, reverse shell, env harvest, or a
  package-runner-fetched payload in a test/hook/lifecycle script).
- Invisible-Unicode or bidi hidden instructions anywhere in the bundle.
- Memory-file poisoning (persistent adversarial writes to `MEMORY.md`/`SOUL.md`/`CLAUDE.md`).
- An obfuscated/packed payload that the static layer cannot read **and** a sandbox run could not clear.
- A post-approval mutation of the bundled surface (definition-hash mismatch) on a re-review — treat as untrusted
  until re-assessed from scratch.

## Coverage is part of the verdict

Record which modes and scanners actually ran. A skill you could only source-review (no sandbox) cannot be rated
"clean on the developer-execution surface" — it is "no static malice found; dynamic behavior un-observed." Every
un-run check is a stated limitation that bounds the claim, never a silent skip.
