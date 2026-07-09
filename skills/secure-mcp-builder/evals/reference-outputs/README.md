# Reference outputs (grading fixtures)

Gold outputs for the three prompts in `../evals.json`, one file per eval id. Same
role as the review skill's fixtures: **calibration aids for grading**, not skill
content. They show what a passing response looks like so a grader can judge a
fresh run against the eval's assertions. Kept out of `references/` on purpose —
a worked example in the read-path makes the agent copy the sample instead of
reasoning from the actual build request.

| Eval | Prompt | Reference output |
|---|---|---|
| 1 `remote-build-threat-model-first` | Wrap internal ticketing, remote multi-user, SSO | `1-remote-build-threat-model-first.md` |
| 2 `refuse-passthrough-and-god-tool-constructively` | "run_request + forward the user's token, ship it" | `2-refuse-passthrough-and-god-tool.md` |
| 3 `consolidate-and-rebuild-with-exclusion-tests` | Three community ticketing servers → one secure replacement | `3-consolidate-and-rebuild.md` |

> **Status: drafts.** Unlike the review skill's fixtures (which came from prior
> testing), these were authored to match the eval prompts and have not been
> validated against live runs. Review before relying on them as gold.

These illustrate shape and rigor, not fixed correct answers. The eval subject
(a ticketing system) is only an example; the skill is vendor-neutral.

**Packaging:** exclude this `reference-outputs/` folder from the shipped `.skill`
— it is a development/grading fixture, not runtime content. Ship `evals.json` so
the SKILL.md reference resolves; leave these out.
