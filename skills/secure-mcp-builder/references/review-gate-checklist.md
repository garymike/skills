# MCP Server Review Gate Checklist

Complete for every server before ship and after any material change. Every MUST passes or the server does not deploy. Attach the completed checklist, the threat model, and both eval scorecards to the change request. Reviewer must not be the author.

**Server:** | **Version:** | **Author:** | **Reviewer:** | **Date:**

## Gate A: Documentation present

- [ ] Threat model complete (`docs/threat-model.md`), all sections filled, lethal trifecta decided
- [ ] ADRs present for language, transport, and auth-pattern decisions
- [ ] README documents purpose, configuration, required scopes, deployment model, data classification
- [ ] Server registered in your MCP inventory (SUP-4)
- [ ] Capability eval scorecard and security test results attached

## Gate B: Authentication and authorization

- [ ] (Remote) RFC 9728 metadata served; bearer validation on every request; `aud` enforced (AUTH-1)
- [ ] No token passthrough anywhere; grep for forwarding of the inbound Authorization header (AUTH-2)
- [ ] Downstream calls use token exchange or scoped identity with per-call user entitlement checks (AUTH-3/5)
- [ ] Sessions never used for authentication; no security decision reads a session ID (AUTH-4, ST-1)
- [ ] Per-tool scope checks present and tested (AUTH-8); tool discovery scope-filtered where implemented, with user-scoped caching (AUTH-10)
- [ ] (OAuth proxy) Per-client consent, exact redirect URI match, state lifecycle per AUTH-6
- [ ] (Local) stdio transport; no unauthenticated listener; credential hygiene per AUTH-9

## Gate C: Input, output, and injection

- [ ] Server-side validation on every parameter beyond schema (INP-1); bounds on all sizes/counts (INP-6)
- [ ] Parameterized data access only (INP-2); no shell interpolation (INP-3); path confinement (INP-4)
- [ ] SSRF controls on every server-side fetch: HTTPS, IP-range denial incl. metadata, redirect validation, DNS pinning, size/time caps (INP-5)
- [ ] Errors sanitized and actionable; no stack traces, hostnames, or secrets in any tool output (OUT-1)
- [ ] Tool results field-allowlisted; PII/secret redaction applied where the backing data warrants it (OUT-5)
- [ ] Upstream content demarcated as untrusted data with instruction-markup stripped; tool metadata static and code-reviewed (OUT-2/3)
- [ ] Tool-definition manifest published for the release; ST-4 message-signing decision documented in the threat model (SUP-6, ST-4)
- [ ] Annotations (`readOnlyHint`/`destructiveHint`/`idempotentHint`/`openWorldHint`) verified truthful per tool
- [ ] Destructive operations are separate tools designed for confirmation flows (AGT-2)

## Gate D: Secrets, logging, supply chain

- [ ] No secrets in code, repo, images, descriptions, or logs; startup fails closed (SEC-1/2)
- [ ] Structured audit log per invocation with principal and redaction; denials logged as security events (LOG-1/2/4)
- [ ] Dependencies pinned; vuln scan and SAST green in CI; SBOM generated (SUP-1/2)
- [ ] (Containerized) non-root, minimal image, egress policy defined (SUP-3)

## Gate E: Testing evidence

- [ ] Security battery (injection, SSRF, authz, resource, handle replay, prompt injection probe) automated and green
- [ ] Capability suite passing at the agreed threshold, held-out tasks included
- [ ] Rate limits and timeouts demonstrated under test

## Gate F: Forward compatibility

- [ ] No server-side per-session state; cross-call state is signed, user-bound, expiring handles (ST-2)
- [ ] No new dependencies on Roots, Sampling, or Logging protocol features
- [ ] SDK version pinned; 2026-07-28 migration notes recorded if applicable

## Sign-off

Reviewer attestation: ______________________  Result: SHIP / BLOCK  Findings ticket(s): ______
