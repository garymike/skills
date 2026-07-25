# MCP Security Assessment — helpdesk-mcp
**DO NOT CONNECT** · **CRITICAL RISK** (2.8)

## Executive summary
1 Critical · 0 High · 1 Moderate · 0 Low · 0 Info

helpdesk-mcp is a first-party remote server fronting the corporate ticketing system, expanding from a pilot to company-wide rollout. It declares Enterprise-Managed Authorization to satisfy the planned centralized-access requirement, but its Authorization Server accepts any validly-signed ID-JAG regardless of audience, so a token minted for any other application in the same IdP tenant is accepted here too. That is worse than not declaring EMA at all: it creates the appearance of centralized enterprise control while remaining bypassable.

**Top findings**
- **CRITICAL** Enterprise-Managed Authorization declared but ID-JAG audience is never validated (Finding-01)
- **MODERATE** Excess OAuth scope requested for a single-purpose tool (Finding-02)

**Scope:** Assess helpdesk-mcp before expanding it from the platform-team pilot to company-wide use.

_Full review · modes code · 2026-07-21 · checks not performed: 2_

## Recommendations
1. Fix ID-JAG audience validation before any expansion beyond the pilot: pass this server's resource identifier as the required audience and reject mismatches, then re-verify with a forged wrong-audience token. (findings Finding-01 · AUTH-11, AUTH-1)
2. Split the requested OAuth scope into tickets.read and tickets.write; drop tickets.admin. (findings Finding-02 · AUTH-8)

## Findings

### Finding-01 — Enterprise-Managed Authorization declared but ID-JAG audience is never validated  ·  CRITICAL  ·  _reasoned_
- **Category:** Token Exposure / Broken Authorization · Part D · AUTH-11, AUTH-1
- **Affected:** Authorization Server: validate_id_jag()
- **Description:** The server declares io.modelcontextprotocol/enterprise-managed-authorization in its initialize response, so a connecting client's administrator will treat it as governed by centralized IdP policy. Its token-validation function verifies the ID-JAG's signature against the IdP's JWKS and checks expiration, but never checks the aud claim against this server's own resource identifier.
- **Impact:** Any validly-signed ID-JAG issued by the same IdP tenant for a different application is accepted here. An attacker, or a compromised, unrelated internal app, that can obtain any ID-JAG from this IdP gains a valid access token to the ticketing system, entirely bypassing the per-server policy the IdP admin believes they configured. This is a confused-deputy, audience-confusion bypass of the exact control EMA exists to provide.
- **Likelihood:** Moderate to high: any other EMA-aware application in the same enterprise IdP tenant is a viable source of a wrong-audience ID-JAG; no privileged access is required to obtain one, only a connection to any other org-approved MCP server or app under the same IdP.
- **Evidence:** `auth/validate.py:41`
  ```
  def validate_id_jag(token: str) -> dict:
      header = jwt.get_unverified_header(token)
      key = jwks_client.get_signing_key(header["kid"])
      claims = jwt.decode(token, key.key, algorithms=["RS256"])
      # no audience=... kwarg: PyJWT does not check aud unless told to
      return claims
  ```
- **Remediation:** Pass audience="helpdesk-mcp" (this server's canonical resource identifier) to jwt.decode, and reject any ID-JAG whose aud does not match. Add a test that presents a validly-signed, wrong-audience token and asserts rejection before re-enabling the EMA declaration. (AUTH-11, AUTH-1)
- **Status:** open

### Finding-02 — Excess OAuth scope requested for a single-purpose tool  ·  MODERATE  ·  _reasoned_
- **Category:** Excessive Agency · Part D · AUTH-8
- **Affected:** tool: helpdesk_close_ticket
- **Description:** The server requests the tickets.admin scope for the entire tool surface, but only helpdesk_close_ticket needs write access; the other four tools are read-only.
- **Impact:** Any compromise of the server's token, or a confused-deputy call routed through it, carries admin-level ticketing scope rather than the narrow write scope the toolset actually needs.
- **Remediation:** Split into tickets.read (the four read tools) and tickets.write (helpdesk_close_ticket only); drop tickets.admin entirely. (AUTH-8)
- **Status:** open

## Technical assessment
- **Purpose:** Expose the corporate ticketing system (create, search, and close helpdesk tickets) to agents company-wide.
- **Creator Publisher:** first-party (Platform Engineering)
- **Maintenance Signals:** Active internal repo, weekly releases, 3 maintainers.
- **License:** internal

| Tool | Function | Class |
|---|---|---|
| `helpdesk_search_tickets` | Search tickets by status, requester, or text. | read |
| `helpdesk_get_ticket` | Fetch a single ticket by id. | read |
| `helpdesk_list_queues` | List ticket queues the caller can see. | read |
| `helpdesk_create_ticket` | Open a new ticket in a queue. | write |
| `helpdesk_close_ticket` | Close a ticket with a resolution note. | write |

- **Auth Client To Server:** oauth21_pkce
- **Auth Downstream:** Service identity with enforced per-user context (AUTH-5) against the ticketing API.
- **Token Passthrough:** False
- **Ema Status:** verified_broken
- **Stored Credential Risk:** low
- **Notes:** OAuth 2.1/PKCE and per-user downstream context are sound. The critical gap is entirely in ID-JAG audience validation (F-01).

## Risk rating
| Factor | Score |
|---|---|
| Provenance | 1 |
| Capability | 3 |
| Permissions | 4 |
| Hosting Exposure | 2 |
| Auth Strength | 5 |
| Credential Storage | 2 |
| Install Vector | 1 |
| Code Hygiene | 2 |
| **Composite** | **2.8** |

Overrides: ema_status: verified_broken -> CRITICAL, recommendation do_not_connect

## Limitations & disclaimer
Point-in-time assessment (2026-07-21) against the reviewed commit. Static/code review only; the Authorization Server was not exercised live with a forged token in this pass. This report is not a warranty.

F-01 is reasoned (static/definition review): the missing audience check is visible in source, not confirmed by presenting a live forged token. Run the skill-security-review validator, or a live authorization-attack pass, to upgrade to confirmed.

Checks not performed (coverage gaps): part-e-runtime, sandbox.
