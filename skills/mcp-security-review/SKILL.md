---
name: mcp-security-review
description: Assess ANY MCP server (vendor, open-source, bespoke, first-party, local or remote/managed) as a senior security and AI architect and produce a standardized, risk-rated security assessment report (identity, capabilities, permissions, hosting, auth, credential risk, findings, computed rating). Use when someone asks to review, assess, vet, audit, risk-rate, or check the safety of an MCP server, connector, or integration, asks is it safe to connect X, mentions tool poisoning, rug pulls, or hardcoded secrets in an MCP, or wants an MCP risk report; covers first-time and re-assessments of already-connected servers. Do NOT use to build or modify servers; use secure-mcp-builder for construction.
---

# MCP Security Review

Assess any MCP server the way a senior security and AI architect would, and deliver a compact, standardized report a decision-maker can act on — a vendor SaaS connector, an open-source package, or a first-party server built last sprint. The report format is fixed, so assessments stay comparable across servers and capturable into a register later.

Core stance: **an MCP server is code with a language-model-shaped injection surface.** Its tool descriptions and schemas execute inside the agent's context; its process runs on a host, or its endpoint receives tokens. Assess all of it, not just the code.

## Workflow

### 1. Identify and gather

Establish exactly what is being assessed. Collect (search the web, registries, and repos as needed; ask the requester only for what you cannot find):

- Name, creator/publisher, source links (GitHub/registry/vendor page), exact version or endpoint.
- Release and maintenance signals: last update, release cadence, maintainer count, issue responsiveness.
- Deployment reality: where and how it runs (local stdio, local HTTP, remote managed, remote self-hosted), and every place it CAN be installed.
- The full tool/capability surface: tools, resources, prompts, and any extensions (Tasks, Apps, sampling/elicitation). Pull the actual definitions, not the marketing page.
- Requested permissions: OAuth scopes, API permissions, filesystem/network reach.
- Protocols: MCP spec version targeted, transport(s), auth mechanism.

**Choose your review mode(s) from `references/review-methods.md` by what access you have:** a GitHub/registry link or source (code review), a live endpoint (remote review), or an installable package (sandbox review). The modes are complementary — each is blind to what the others catch, so reconcile them where you can, and a repo-vs-live divergence is itself a finding. Given a GitHub link, clone at a pinned commit (record the SHA as the point-in-time anchor), enumerate tool definitions from source, and run the secret/dependency scans. Record which modes and scanners you actually used (`review-methods.md` maps each missing tool to its manual fallback); coverage bounds what your findings can claim, and any gap is a stated limitation, not a silent skip.

Assign assessment depth from `references/risk-tiering.md`: a read-only public-data server gets a fast pass; anything credentialed, write-capable, or touching sensitive data gets the full inspection.

### 2. Inspect

Work `references/inspection-checklist.md` at the assigned depth, using the mode(s) chosen above (`review-methods.md` maps each mode to the parts it can satisfy: code review drives Parts A/C, live review Parts B/D, sandbox the Part C/E runtime checks):

- **Part A** Provenance and package integrity (typosquats, repo↔package match, dependency scan, CVE/incident history, vendor posture).
- **Part B** Tool surface as injection surface: automated scan (mcp-scan or equivalent) plus a human read of every description and schema; hash the definition set.
- **Part C** Code and runtime (local/self-hosted, or first-party with source access): startup behavior, filesystem/network reach, credential handling, subprocess and dynamic-code use, sandbox observation. **Hardcoded secrets, credentials in config, or tokens in logs are automatic Critical findings.**
- **Part D** Auth and data flow: auth mechanism quality (OAuth 2.1/PKCE vs static keys vs nothing), token handling (passthrough is an automatic Critical), stored credential risk (where secrets live at rest, encrypted how, revocable how), data egress and retention.

### 3. Assess composition (when connection context is known)

If the assessment is for connecting the server into a real environment, run `references/composition-risks.md`: the lethal trifecta (Simon Willison's term) across the combined connected set, tool shadowing, cross-server data flows, aggregate scope. If assessing in the abstract (no target environment), state the composition preconditions in the report instead ("completes the trifecta for any population that also holds private-data access").

### 4. Compute risk and produce the report

Score per `references/risk-scoring.md` (factor-based, criticals override), then produce the report **data-first**: author a schema-valid `assessment.json` and render it. `references/report-template.md` has the pipeline and the full authoring rules.

- **Author the data, not prose.** Write `assessment.json` to `schema/assessment.schema.json` (the field-by-field contract), then render with `scripts/render_report.py` into HTML + Markdown. Hand-formatting a report is a regression — authoring the data keeps every assessment identical in shape and comparable across servers. The `assessment.json` IS the machine-readable record a future register (a database, or a knowledge base such as a wiki) captures, holding the risk state and the point-in-time definition hash without reparsing prose.
- **Findings lead, structurally.** The renderer fixes section order — a verdict-first executive summary (overall rating, severity counts, top findings) leads, recommendations next, descriptive sections and full findings below. Any Critical or High finding (vulnerability, hardcoded secret, token passthrough, poisoned description, tiering disqualifier) surfaces in that summary.
- **Every field gets a value or an explicit "unknown, because ...";** security-relevant unknowns raise the risk score, never lower it. Critical/High findings carry redacted evidence and control-linked remediation.
- **Validate before shipping.** The source must validate against the schema (the renderer fails closed when `jsonschema` is present), and the rendered report must pass `references/report-quality-rubric.md`. A report nobody trusts protects nobody.

### 5. Optional: decision and lifecycle layer

If this assessment supports a connection request (reviewed and approved by someone other than the requester), complete `references/decision-record-template.md` and follow `references/onboarding-monitoring.md` for pinning, monitoring (definition-hash rug pull detection), re-review triggers, and offboarding. Skip this layer for pure assessments, but always record the definition hash — it is the anchor for every future re-assessment.

## Reference files

| File | Read when |
|---|---|
| `references/review-methods.md` | Step 1, choosing how to ingest the server (GitHub link, live endpoint, sandbox) |
| `references/risk-tiering.md` | Step 1, sets assessment depth; contains automatic disqualifiers |
| `references/inspection-checklist.md` | Step 2 |
| `references/composition-risks.md` | Step 3 |
| `references/risk-scoring.md` | Step 4, the computed-risk model |
| `references/report-template.md` | Step 4, the report pipeline and authoring rules |
| `schema/assessment.schema.json` | Step 4, the field-by-field contract for `assessment.json` |
| `references/report-quality-rubric.md` | Step 4, the ship gate (must-pass + do-not-reintroduce) |
| `references/decision-record-template.md` | Step 5 only |
| `references/onboarding-monitoring.md` | Step 5, re-reviews, offboarding |

## Scripts

- `scripts/render_report.py` — renders a schema-valid `assessment.json` into the
  styled HTML report (plus a Markdown twin, or a shareable PDF via `--pdf`, which
  expands the appendix so the machine-readable record is captured in print). Stdlib-only;
  when `jsonschema` is installed it pre-flight-validates against
  `schema/assessment.schema.json` and fails closed on a violation. This is the Step 4
  output path: author the data, then render.
- `scripts/hash_tool_definitions.py` — deterministic SHA-256 of a server's
  tool-definition set (feed it a `tools/list` result as JSON). Use it in Part B
  and in monitoring so the recorded hash is reproducible on re-review and matches
  a builder-published SUP-6 manifest. The canonicalization is pinned in the
  script; the same file ships in secure-mcp-builder and the two copies must stay
  identical.

## Standards alignment and sources

The inspection checklist and scoring model cover, from the assessor's side, the OWASP MCP Security Cheat Sheet (all 12 sections: least privilege, tool/schema integrity, sandboxing, human-in-the-loop, input/output validation, auth and transport, message integrity, multi-server isolation, supply chain, monitoring, consent/installation, injection via tool returns), the OWASP MCP Top 10, the official MCP spec security best practices, and the OWASP Top 10 for Agentic Applications. When any source adds a control class, fold it into the checklist as a concrete item and re-validate the mapping — the mapping claim above must stay true.

For hands-on technique (traffic interception, injection batteries, authorization attacks), the appsecco pentesting-mcp-servers checklist is the practical companion to Part E.

Sources: cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html; owasp.org/www-project-mcp-top-10; modelcontextprotocol.io/docs/tutorials/security/security_best_practices; genai.owasp.org; github.com/appsecco/pentesting-mcp-servers-checklist; christian-schneider.net (defense-first MCP architecture, sampling and CVE case studies); github.com/MCP-Manager/MCP-Checklists (threat list, RADE, data masking); github.com/slowmist/MCP-Security-Checklist (audit-derived checklist: background persistence, service identity, lifecycle); practical-devsecops.com/mcp-security-checklist (injection prevalence data). The lethal trifecta framing is Simon Willison's (simonwillison.net/2025/Jun/16/the-lethal-trifecta/).

## Relationship to secure-mcp-builder

secure-mcp-builder constructs servers; this skill assesses them, including first-party ones. An independent assessment of a first-party server is healthy and expected: the builder's review gate is the author-side control, this report is the assessor-side view. If an assessment concludes "build it ourselves instead," hand off to secure-mcp-builder.

## Maintaining this skill

- **After any skill revision:** re-run the three eval prompts in `evals/evals.json` and grade against their assertions to catch regressions before redistributing.
- **Quarterly:** re-check the standards and sources above (OWASP MCP Top 10, the cheat sheet, the spec security page, and the real-incident CVE anchors in `risk-tiering.md`); fold new attack classes into the inspection checklist as concrete items, not prose, and re-validate the standards-mapping claim.
- **On MCP spec releases:** refresh the protocol-facing fields the checklist and report template reference (spec version, deprecated features such as Roots/Sampling/Logging, caching and handle rules).
- **Keep in sync with secure-mcp-builder:** `scripts/hash_tool_definitions.py` must stay byte-identical in both skills; Part C's code-hygiene yardstick tracks that skill's `references/security-requirements.md` control catalog; and the trifecta mitigation preference order in `references/composition-risks.md` must match the builder's guidance. A change to any of these is a paired change to both skills.
