# Risk Tiering for Third-Party MCP Servers

Assign the highest tier any single factor triggers. Tier sets review depth, reviewer seniority, and monitoring intensity. When in doubt, tier up: over-tiering costs minutes, under-tiering costs an incident.

## Factors

| Factor | Tier 1 (Low) | Tier 2 (Moderate) | Tier 3 (High) |
|---|---|---|---|
| Data access | Public data only | Internal, non-sensitive | Confidential/restricted, PII, financial, credentials |
| Capability | Read-only | Writes to low-impact systems | Destructive, financial, sends external comms, executes code |
| Credentials | None | Scoped API key, read scopes | OAuth write scopes, broad tokens, service accounts |
| Deployment | Remote, no install | Local install, sandboxed | Local install with host access, or remote receiving org tokens |
| Publisher | Established vendor, signed releases | Known OSS project, active maintenance | Unknown/individual publisher, new package, unsigned |
| Users | Single requester | One team | Org-wide or privileged users |
| Composition | Adds no trifecta leg | Adds one leg to an existing pair | Completes the trifecta for any user population |

## Tier outcomes

- **Tier 1**: fast path (SKILL.md), reviewer sign-off, annual re-review.
- **Tier 2**: full Phases 2-5, reviewer approval, semiannual re-review, gateway policy required for remote.
- **Tier 3**: full review plus a sandbox behavioral run (local) or vendor security assessment (remote), approval by a senior reviewer, conditions expected (scope cuts, user limits, egress restrictions), quarterly re-review, continuous monitoring mandatory.

## Automatic disqualifiers (deny without full review)

- Requests credentials it cannot justify for its stated purpose, or exhibits token passthrough (asks the client to hand it tokens issued for other services).
- Obfuscated, packed, or unreviewable code in a local package; install scripts that fetch and execute remote content.
- Tool descriptions carrying instruction-injection patterns aimed at the model ("ignore", "always call", references to other servers' tools, hidden text).
- Typosquat or impersonation of a known package/vendor.
- Publisher cannot be identified at all for anything above Tier 1 data.

Disqualified requests get a denial record with reasoning; the requester may propose alternatives, including a first-party build via secure-mcp-builder.

## Real-incident anchors

Calibration cases, not an exhaustive list. If the server under review resembles one of these shapes, inspect that surface specifically.

- **Command injection in an OAuth proxy** — a crafted `authorization_endpoint` passed to a shell gave RCE on the client ([CVE-2025-6514](https://jfrog.com/blog/2025-6514-critical-mcp-remote-rce-vulnerability/), mcp-remote).
- **Arbitrary file write + header-based SSRF below the tool layer** — path traversal in attachment tools and unvalidated URL headers ([CVE-2026-27825 / 27826](https://pluto.security/blog/mcpwnfluence-cve-2026-27825-critical/), mcp-atlassian).
- **IDE/client config flaws that fire before the trust prompt** — code execution or key exfiltration from an untrusted repo's config, disclosed by Check Point Research against [Cursor](https://research.checkpoint.com/2025/cursor-vulnerability-mcpoison/) (MCPoison, CVE-2025-54136) and [Claude Code](https://blog.checkpoint.com/research/check-point-researchers-expose-critical-claude-code-flaws/) (CVE-2025-59536, CVE-2026-21852).

The base rate is high: independent audits in early 2026 found command-injection flaws in roughly 40% of the MCP servers examined ([practical-devsecops](https://www.practical-devsecops.com/mcp-security-checklist/)). The Part E injection battery is not optional theater.
