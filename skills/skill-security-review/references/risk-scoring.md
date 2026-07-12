# Risk scoring — the computed-risk model

Factor-based, with **criticals that override**. The score exists to make assessments comparable; the verdict is
what a decision-maker acts on. Never let a tidy numeric score bury a Critical.

## Factors (each scored 0 / 1 / 2 / 3 = none / low / med / high risk)

1. **Developer-execution surface** — auto-run files touching credentials, egress, or dynamic exec. *This factor
   carries the most weight; a 3 here is an automatic Critical (see below).*
2. **Agent-execution surface** — prompt-injection / tool-poisoning / memory-poisoning potential in `SKILL.md` and
   agent-invoked scripts.
3. **Provenance & maintenance** — author/repo/published mismatch, typosquat, abandonment, malicious dependency.
4. **Capability & reach** — how much the skill can touch (filesystem, network, credentials, other skills) if it
   turns hostile.
5. **Obfuscation** — packed/encoded/high-entropy artifacts that resist static reading.

## Criticals override

Any **Critical finding** sets the verdict to **BLOCK / do-not-install** regardless of the factor sum:

- Any developer-execution-surface Critical (Part C) or dynamic-confirmation escape/egress (Part D).
- Invisible-Unicode/bidi hidden instructions; memory-file poisoning; a token/secret hardcoded in the bundle.
- An un-clearable packed payload; a post-approval definition-hash mutation.

## Verdict bands (after criticals)

| Verdict | Meaning |
|---|---|
| **BLOCK** | Any Critical, or an un-observed developer-execution surface on a skill that ships auto-run files. |
| **CAUTION** | No Critical, but med/high factors (broad reach, thin provenance) — install only with the stated mitigations (exclude from test-runner globs, review-before-install, pin + monitor). |
| **CLEAR** | Both surfaces inspected (static + dynamic where warranted), no Critical, low factors. State the coverage that backs the "clear." |

## Honest residual, always

A CLEAR verdict states what was and wasn't exercised. "Static malice clean; not detonated (no sandbox available)"
is CAUTION, not CLEAR. Security-relevant unknowns raise the score; they never lower it.
