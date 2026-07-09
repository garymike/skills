# Reference outputs (grading fixtures)

Gold outputs for the three prompts in `../evals.json`, one set per eval id. These
are **calibration aids for grading**, not skill content: they show what a passing
response looks like so a human or LLM grader can judge a fresh run against the
eval's assertions. They are deliberately kept out of `references/` so the skill
never loads them during a real assessment (a worked example in the read-path makes
the agent copy the sample instead of reasoning from the server under review).

## How the report golds are produced

Full-report assessments (#1, #2) are **data-first**: the assessment is authored as a
schema-valid `assessment.json` and rendered to HTML + Markdown by the pipeline.

```
<name>.assessment.json   # the source of truth — validates against ../../schema/assessment.schema.json
        │  python ../../scripts/render_report.py <name>.assessment.json --html <name>.html --md <name>.rendered.md
        ▼
<name>.html              # styled, print/PDF-ready report
<name>.rendered.md       # Markdown rendering of the same data
```

Grade a fresh run on whether it emits an `assessment.json` that (a) validates against
the schema and (b) carries the right verdict, rating, and findings — not on prose
wording. The `.html` / `.rendered.md` show the shape the renderer guarantees.

| Eval | Prompt | Reference output |
|---|---|---|
| 1 `assess-oss-package-full-report` | arxiv-mcp-server, researchers with a document store + email | `1-assess-oss-package-arxiv.assessment.json` (+ `.html`, `.rendered.md`) |
| 2 `critical-findings-lead-report` | first-party CRM server, hardcoded key + god-tool | `2-critical-findings-crm.assessment.json` (+ `.html`, `.rendered.md`) |
| 3 `rug-pull-reassessment` | approved ticketing connector, definition hash changed | `3-rug-pull-reassessment.md` |

**Why #3 is prose, not an `assessment.json`.** Eval #3 asks for the re-assessment
*process* and the *delta* to an existing report, and the prompt supplies almost no
server specifics. A rug-pull re-assessment amends a record (new hash, diff summary,
any rating change) rather than re-emitting a fresh full report, so its gold is a
workflow narrative. Grade it on the process assertions, not on report shape.

Outputs carry point-in-time specifics (dates, CVEs, scores); treat them as
examples of shape and rigor, not as fixed correct answers to diff against.

**Packaging:** exclude this `reference-outputs/` folder from the shipped `.skill`
— it is a development/grading fixture, not runtime content. Ship `evals.json` so
the SKILL.md reference resolves; leave these out.
