# Changelog

All notable changes to this repo are documented here. Versions match the
`version` field in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-07-11

### Changed
- **skill-security-review:** corrected the developer-execution-surface framing from "the blind spot every skill
  scanner misses" to the accurate "a surface advisory scanners flag but don't *gate* on." SkillSpector v2.3+ scans
  bundled `.husky/`/`package.json` and reports the payload (HIGH), but exits 0 (no fail-on), so a CI gate on exit
  codes still lets it through; the enforcing gate (`skill-testfile-gate`) is what stops it, and the research SOTA
  still misses the surface by scope. Wording only; the two-surface methodology is unchanged.

## [0.4.0] - 2026-07-11

### Added
- **skill-security-review** (new, model-invoked): assess any agent skill across both execution surfaces: the
  agent-execution surface (`SKILL.md` + agent-invoked scripts: prompt injection, tool poisoning, memory poisoning)
  and the **developer-execution surface** (bundled test files, git hooks, npm/pip lifecycle scripts that auto-run
  on `npm test` / `git commit` / `npm install`, outside the agent, the blind spot skill scanners miss). Ships a
  two-surface inspection checklist, factor-based risk scoring (developer-execution criticals override), a data-first
  report pipeline with `schema/assessment.schema.json` (`skill-assessment/v1`), and
  `scripts/hash_skill_definitions.py` for rug-pull detection. The assessor-side methodology behind the
  `skill-auditor` agent ([security-agents](https://github.com/garymike/security-agents)); sibling of
  `mcp-security-review`.

## [0.3.2] - 2026-07-08

### Changed
- **secure-mcp-builder:** harden deployment/supply-chain controls against the Wiz
  MCP security best-practices cheat sheet. `SUP-2` now names Sigstore/cosign + SLSA
  attestation and CI rejection of unsigned artifacts; `SUP-3` adds seccomp/AppArmor,
  `no-new-privileges` + capability drop, and CPU/memory limits (denial-of-wallet);
  `ST-3` and the gateway-topology guide name mutual TLS (mTLS) for fronted and
  service-to-service deployments; the review-gate checklist mirrors the expanded
  `SUP-3`. Added Wiz to the sources list.

## [0.3.1] - 2026-07-08

### Changed
- **secure-mcp-builder:** add explicit third-party attribution for the bundled
  capability-eval harness (`scripts/evaluation.py`, `scripts/connections.py`), adapted
  from the `mcp-builder` skill in anthropics/skills (Apache-2.0). Adds per-file
  "modified from" headers and a third-party note in the README License section
  (Apache-2.0 §4(b)/(c) compliance). No functional change.

## [0.3.0] - 2026-07-08

### Added
- **mcp-security-review** skill: assess any MCP server (vendor, open-source, or
  first-party) as a security architect and produce a standardized, risk-rated
  assessment: review modes (code / live / sandbox), a computed risk model, and a
  schema-valid `assessment.json` rendered to HTML + Markdown. Previously developed
  privately; now public.
- **secure-mcp-builder** skill: design, threat-model, build, and harden
  production-grade MCP servers (Python or TypeScript, stdio or remote HTTP) through
  four phases with a required threat model and review gate, a normative
  security-requirements catalog, and a bundled capability-eval harness. Previously
  developed privately; now public.

## [0.2.1] - 2026-07-02

### Added
- **github-profile:** substance-intake prompts: Signature achievements
  (quantified), Credentials, and Collaboration.
- **github-profile:** assembly rule preferring quantified impact over adjectives.
- **github-profile:** privacy guard so a private repo's name or description is
  never surfaced in a public README without explicit confirmation.
- Release tracking: `CHANGELOG.md` and a Releases convention in `CLAUDE.md`.

## [0.2.0] - 2026-07-02

### Added
- **github-security-audit** skill: audit and harden a GitHub account and its
  repositories, then fix findings interactively.

## [0.1.0] - 2026-07-02

### Added
- Initial skills repo with the **github-profile** skill: design, build, and
  deploy a GitHub profile README.
