# Changelog

All notable changes to this repo are documented here. Versions match the
`version` field in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-07-21

### Added
- **mcp-security-review: Enterprise-Managed Authorization (EMA) awareness.** New
  `ema_status` field on `technical_assessment.authentication_and_credential_risk`
  (not_declared / declared_unverified / verified_correct / verified_broken),
  additive so every existing recorded assessment stays schema-valid unmodified.
  New Part D checklist item: check whether a server declares
  `io.modelcontextprotocol/enterprise-managed-authorization`, and if so, verify
  (source or live) that it actually validates the ID-JAG's signature, issuer,
  expiration, `aud` (the Resource Authorization Server's own issuer identifier)
  and `resource` (the MCP server's canonical resource identifier). A
  declared-but-broken implementation is now an automatic Critical override in
  `risk-scoring.md`, worse than not declaring the extension at all: it creates
  false assurance that centralized IdP policy is enforced. New eval 4
  (`broken-ema-audience-check`) exercises a first-party server whose ID-JAG
  validation checks neither `aud` nor `resource`, a real, common PyJWT gotcha,
  and confirms the override forces CRITICAL / do_not_connect even though the
  raw weighted composite would otherwise round to MODERATE.
- **secure-mcp-builder: AUTH-11, Enterprise-Managed Authorization.** New control
  (SHOULD, remote HTTP, enterprise deployment), scoped like AUTH-7 rather than a
  blanket MUST since real-world EMA adoption is about a month old with one
  identity provider (Okta). If declared, ID-JAG validation must meet the same
  bar AUTH-1 already sets for bearer tokens (JWKS signature, `iss`, `exp`,
  `aud` against the Resource Authorization Server's own issuer identifier, and
  `resource` against this server's canonical resource identifier: two distinct
  claims, two distinct values, and `resource` is the one that says the token is
  for you). A short addendum to `auth-patterns.md` Pattern A (not a new pattern,
  since EMA is the same resource-server shape with an added grant type), and a
  new ship-gate line in `review-gate-checklist.md`: declaring AUTH-11 without
  confirmed-correct validation does not pass review.

Trigger: MCP's Enterprise-Managed Authorization extension went stable on
2026-06-19 (github.com/modelcontextprotocol/ext-auth), replacing per-server
OAuth consent with IdP-centralized policy for enterprise deployments.

### Changed
- **secure-mcp-builder: em-dash cleanup** in `auth-patterns.md` and
  `security-requirements.md`. Three pre-existing lines reworded to drop stray
  em-dashes the earlier plain-language pass missed. Wording only, no semantic
  change to any control.

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
