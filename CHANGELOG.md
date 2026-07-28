# Changelog

All notable changes to this repo are documented here. Versions match the
`version` field in `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-07-28

### Fixed
- **Tool-definition hashing missed the MCP Apps declaration.** MCP's 2026-07-28
  spec declares a tool's interactive UI in `_meta.ui.resourceUri`, which
  `sha256-canon-v1` did not hash, so a server could repoint an approved tool at
  entirely different UI without changing its definition hash: a rug pull through
  the control this project treats as its highest-value one.
  `hash_tool_definitions.py` (both copies, which stay byte-identical) now hashes
  `_meta.ui` and reports `sha256-canon-v2`. Only `_meta.ui` is hashed, never the
  whole open `_meta` namespace, so benign metadata churn does not fire.
  **Migration:** a v1 hash and a v2 hash of the same unchanged tool set differ;
  that alone is not a rug-pull signal. Re-baseline once at v2, then compare v2 to
  v2, and record the algorithm id alongside the hash (the `--set-hash-only` flag
  prints a bare hash with no algorithm context, so a decision record holding only
  that value cannot tell the two apart). Honest scope: the tool carries only the
  `resourceUri` pointer, so a widened CSP on the UI resource is not detected by
  the hash and needs the new manual review step.

### Added
- **mcp-security-review: coverage for the 2026-07-28 stateless spec.** Three
  optional fields, all additive so recorded assessments stay valid unmodified:
  `handle_security` on the auth block, `tasks_status` and `mcp_apps_status` on the
  protocols block. Four checklist items, each beside its nearest existing sibling:
  MCP Apps in Part B, routing-header hygiene and Tasks resource discipline in Part
  C, stateless handle security in Part D. Two overrides force CRITICAL,
  `mcp_apps_status: reviewed_unsafe` and `handle_security: verified_broken`, both
  authorization or injection bypasses. `tasks_status` deliberately gets no
  override: unbounded task creation is an availability problem, and forcing a
  verdict on it would be crying wolf. New eval 5 (`unsafe-mcp-app-csp`) exercises
  the MCP Apps override against a server whose every problem lives on the UI
  resource rather than the tool definition, the exact failure the definition hash
  cannot see.
- **secure-mcp-builder: SEC-5, UI-1, and AGT-5.** `SEC-5` (MUST, remote HTTP)
  keeps credentials and PII out of the `Mcp-Method` and `Mcp-Name` routing headers
  every proxy and log captures, and requires rejecting header/body mismatches.
  `UI-1` opens a new control family for MCP Apps: static reviewed UI artifacts, no
  HTML built from runtime data, CSP limited to origins you control, minimal
  permissions. `AGT-5` bounds the Tasks extension, since a task outlives the
  request `INP-6` bounds, and the spec makes `tasks/cancel` cooperative so
  status-only cancellation is compliant and still strands work. Stateless handles
  get no new control: `ST-1` and `ST-2` already cover them. `SUP-6` now states that
  the manifest covers `_meta.ui` but that each UI resource needs its own hash.
- The repo's first mechanical test (`test_hash_tool_definitions.py`), stdlib-only
  to match the script it covers.

### Changed
- **secure-mcp-builder: the recommended build target is now 2026-07-28.**
  `spec-versions.md` previously labelled 2025-11-25 as the build target while the
  2026 revision was still a release candidate. Now that it is final, new servers
  should target it, with 2025-11-25 kept as a documented fallback where SDK or
  client support is not yet there. This changes what builders are told to build
  against, so it is called out rather than folded into the currency pass.
- **mcp-security-review: report labels for the three new fields.**
  `render_report.py` gained explicit `LABELS` entries for `tasks_status`,
  `mcp_apps_status`, and `handle_security`, so they render as "Tasks status",
  "MCP Apps status", and "Handle security" rather than falling through to
  title-casing, which produced "Mcp Apps Status" and mis-cased the acronym. All
  four reference outputs re-rendered.

## [0.5.1] - 2026-07-26

### Fixed
- **mcp-security-review: render `permissions`, `hosting`, and `protocols`.** These three
  `technical_assessment` fields were schema-valid but never reached either report body,
  HTML or Markdown, only the raw JSON appendix; pre-existing since the skill's original
  2026-07-08 publish. Both renderers now show a subsection for each, in the schema's
  declared field order.
- **mcp-security-review: Markdown report parity with HTML.** `render_md` built field
  labels and boolean values inline instead of through the shared `label()`/`fmt_val()`
  helpers `render_html` already used, so `ema_status` showed as "Ema status" in Markdown
  against "EMA status" in HTML, and `token_passthrough` showed Python's `True`/`False`
  instead of "Yes"/"No". Both formats now derive from the same helpers, plus a new
  `prep_kv()` shared by both for the hosting/protocols fields, so hardcoding either
  renderer's exact key list can no longer let a schema-valid extra key silently vanish
  from one format but not the other.
- **mcp-security-review: Markdown auth section had no heading.** A first attempt at the
  fix above gave Permissions, Hosting, and Protocols their own bold headings but left the
  existing authentication section unlabeled; under CommonMark, a blank line alone does
  not end a bullet list, so the auth fields, including `ema_status`, rendered as trailing
  items of the Protocols list rather than their own section. Caught by an independent
  review before merge and verified fixed with a CommonMark-compliant parser.
- Two em-dashes fixed in `evals/evals.json` and `evals/reference-outputs/2-critical-findings-crm.assessment.json`;
  the latter was in the `permissions` field, previously invisible since permissions was
  never rendered before this fix.

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
