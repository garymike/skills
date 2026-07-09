# MCP Security Assessment — crm_mcp
**DO NOT CONNECT** · **CRITICAL RISK** (4.6)

## Executive summary
1 Critical · 1 High · 1 Moderate · 0 Low · 0 Info

crm_mcp is a first-party stdio server exposing the CRM to agents. A live production credential is committed to source, and its single tool executes arbitrary model-supplied queries — either one alone is disqualifying. Blast radius is the full read scope of the shared key, with no per-user attribution. Clean dependency scans do not offset this.

**Top findings**
- **CRITICAL** Live production credential committed to source (Finding-01)
- **HIGH** Arbitrary-query god-tool grants unbounded CRM access to the model (Finding-02)

**Scope:** Assess the first-party crm_mcp server before expanding it beyond the pilot group.

_Full review · modes code · 2026-07-03 · checks not performed: 2_

## Recommendations
1. Rotate the CRM credential today and audit its historical use — the key is in git history and every clone, so deletion is not remediation. (findings Finding-01 · SEC-1, SEC-2)
2. Move secret handling to a secrets manager with runtime injection and fail-closed startup. (SEC-1, SEC-2)
3. Replace crm_run_query with constrained, single-responsibility tools; route the redesign through secure-mcp-builder (threat model + review gate) before expansion. (findings Finding-02 · AGT-4)
4. Add per-user entitlement and structured audit logging before any population beyond the pilot. (findings Finding-03 · AUTH-5, LOG-1)

## Findings

### Finding-01 — Live production credential committed to source  ·  CRITICAL  ·  _reasoned_
- **Category:** Credential / Token Exposure · Part C · SEC-1
- **Affected:** config.py
- **Description:** A live CRM API key is hardcoded in config.py and committed to the repository.
- **Impact:** Anyone with a clone or laptop access obtains full CRM API access. The key is in git history, so removing it from HEAD is not remediation.
- **Likelihood:** Trivial — the key is in plaintext in the tracked repo.
- **Evidence:** `config.py:14`
  ```
  CRM_API_KEY = 'sk-live-••••••••'
  ```
- **Remediation:** Rotate the credential now (not just delete it), then reissue via a secrets manager with runtime injection and fail-closed startup. (SEC-1, SEC-2)
- **Status:** open

### Finding-02 — Arbitrary-query god-tool grants unbounded CRM access to the model  ·  HIGH  ·  CVSS 8.7  ·  _reasoned_
- **Category:** Excessive Agency / Injection · Part C · AGT-4
- **Affected:** tool: crm_run_query(query)
- **Description:** The sole tool executes model-supplied queries against the CRM with no constraint, allowlist, or templating.
- **Impact:** Any prompt injection anywhere in the agent's context becomes a CRM query engine; the blast radius is the full read scope of the key.
- **Likelihood:** High — reachable by any injected instruction.
- **Evidence:** `tools/query.py:22`
  ```
  def crm_run_query(query: str):
      return crm.execute(query)   # unconstrained, model-supplied
  ```
- **Remediation:** Replace with constrained, single-responsibility tools (crm_search_accounts, crm_get_opportunity, ...) with typed, bounded parameters. If a query escape hatch is genuinely required, allowlist-template it — never free-form. (AGT-4)
- **Status:** open

### Finding-03 — No per-user authorization or attribution (confused deputy)  ·  MODERATE  ·  _reasoned_
- **Category:** Part D · AUTH-5
- **Affected:** shared service key
- **Description:** A single shared key means every pilot user acts with identical CRM reach and no per-user audit attribution.
- **Impact:** A compromised or confused agent acts with the full shared scope, and there is no per-user accountability.
- **Remediation:** Enforce per-user entitlement via token exchange or enforced user context, and add structured audit logging. (AUTH-5, LOG-1)
- **Status:** open

## Technical assessment
- **Purpose:** Exposes the CRM to agents for the pilot group.
- **Creator Publisher:** first-party
- **Maintenance Signals:** Active internal repo; dependencies pinned, scan clean.
- **License:** internal

| Tool | Function | Class |
|---|---|---|
| `crm_run_query` | Executes model-supplied queries against the CRM | read |

- **Auth Client To Server:** none
- **Auth Downstream:** static hardcoded API key
- **Token Passthrough:** False
- **Stored Credential Risk:** critical
- **Notes:** Compromise of any clone equals full CRM access; revocation currently means rotating a key that is in git history.

## Risk rating
| Factor | Score |
|---|---|
| Provenance | 1 |
| Capability | 5 |
| Permissions | 4 |
| Hosting Exposure | 3 |
| Auth Strength | 4 |
| Credential Storage | 5 |
| Install Vector | 2 |
| Code Hygiene | 4 |
| **Composite** | **4.6** |

Overrides: hardcoded live secret -> CRITICAL; arbitrary-query god-tool -> High

## Limitations & disclaimer
This is a point-in-time static assessment (code review only) of the pinned source. It is not a warranty. Findings require independent verification before remediation decisions rely on them.

Findings are marked `reasoned` (identified by static review); none were reproduced with a live proof-of-concept. Run the validator skill to confirm exploitability and collect supporting evidence.

Checks not performed (coverage gaps): part-e-runtime, live-auth-testing.
