# Report template — the data-first pipeline

Author the **data**, not prose. Write a schema-valid `assessment.json` (`schema/assessment.schema.json` is the
field-by-field contract), then present it findings-first. Hand-formatting a report is a regression: the data keeps
every assessment identical in shape and comparable across skills, and the `assessment.json` IS the machine-readable
record a register captures (risk state + point-in-time definition hash) without reparsing prose.

## Section order (fixed, findings-first)

1. **Verdict summary** — overall verdict (BLOCK / CAUTION / CLEAR), severity counts, the top findings, and the
   **coverage line** (which surfaces + scanners actually ran). Any developer-execution Critical surfaces here.
2. **Recommendations** — control-linked, actionable (e.g., "exclude `.claude/`, `.cursor/` from test-runner
   globs"; "do not install — `postinstall` reads `~/.ssh`"; "pin @<sha> and monitor the definition hash").
3. **Skill identity** — name, author, source, pinned commit, version, install/trigger model, definition hash.
4. **Surface inventory** — what the bundle ships (SKILL.md, scripts, tests, hooks, lifecycle scripts, commands),
   flagged per the checklist.
5. **Findings** — each with: surface (agent-execution / developer-execution / provenance / composition), severity,
   redacted evidence (file:line), and control-linked remediation.
6. **Coverage & limitations** — modes and scanners run vs not; every un-run check stated.

## Authoring rules

- **Every field gets a value or an explicit `"unknown, because …"`.** Security-relevant unknowns raise the score.
- **Findings carry redacted evidence.** A Critical names the file and line (`.husky/pre-commit:12`) and the exact
  pattern, with any secret redacted — enough to act on, nothing re-weaponizable.
- **The verdict must match the scoring.** A CLEAR verdict states the coverage that backs it; an un-detonated
  auto-run surface caps at CAUTION.
- **Validate before shipping.** `assessment.json` must validate against the schema. A report nobody trusts protects
  nobody.

## Minimal shape

```json
{
  "schema": "skill-assessment/v1",
  "skill": { "name": "...", "source": "...", "pinned_commit": "...", "definition_sha256": "..." },
  "verdict": "BLOCK | CAUTION | CLEAR",
  "severity_counts": { "critical": 0, "high": 0, "medium": 0, "low": 0 },
  "coverage": { "modes": ["source"], "scanners": ["skill-testfile-gate", "skillspector"], "detonated": false },
  "surfaces": { "agent_execution": [], "developer_execution": [] },
  "findings": [
    { "surface": "developer_execution", "severity": "critical", "title": "...",
      "evidence": ".husky/pre-commit:12", "remediation": "..." }
  ],
  "score": { "factors": {}, "total": 0 },
  "limitations": ["..."]
}
```
