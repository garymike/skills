# MCP Security Assessment — arxiv-mcp-server
**CONNECT WITH CONDITIONS** · **MODERATE RISK** (1.85)
Source: <https://github.com/blazickjp/arxiv-mcp-server/tree/7f3c9e2a1b4d6c8e0f2a4b6d8c0e2f4a6b8d0c2e>
Provenance: Known OSS — ★ 412 · 47 forks · original · 380 followers · 41 repos · since 2019 · updated 2026-06

## Executive summary
0 Critical · 2 High · 0 Moderate · 0 Low · 0 Info

arxiv-mcp-server is a read-only, no-credential local server that fetches public arXiv papers into model context. Its own risk is low, but for the requesting population — who already hold a document store and email connectors — it adds the untrusted-content leg and completes the lethal trifecta. That composition risk, plus a name collision and an individual-maintainer supply chain, drive the rating; the conditions below reduce it.

**Top findings**
- **HIGH** Composition completes the lethal trifecta for the requesting population (Finding-01)
- **HIGH** Cross-registry name collision invites a supply-chain swap (Finding-02)

**Conditions to proceed**
- Managed install only: package the pinned PyPI version internally and block ad-hoc npm/npx installs of this name.
- Break the trifecta for the pilot: require confirmation on email-send in any session where read_paper has fired, or limit the pilot to users without the email connector.
- Run a sandbox verification before rollout: confirm egress is arxiv.org only and record the tool-definition hash.

**Scope:** Assess arxiv-mcp-server for researchers who already have a document store and email connectors.

_Standard review · modes code · 2026-07-02 · checks not performed: 1_

## Recommendations
1. Managed install only — publish the pinned PyPI version internally and block ad-hoc npm/npx installs of this name (name-collision defense). (findings Finding-02)
2. Break the trifecta for the pilot population: gateway/client policy requiring confirmation on email-send once read_paper has fired, or restrict the pilot to users without the email connector. (findings Finding-01)
3. Sandbox verification run before rollout: confirm egress is arxiv.org only; record the tool-definition hash for rug-pull monitoring.
4. Register in the inventory, wire definition-hash monitoring, and re-assess on version bump or in 12 months.

## Findings

### Finding-01 — Composition completes the lethal trifecta for the requesting population  ·  HIGH  ·  _reasoned_
- **Category:** Excessive Agency / Data Exfiltration · Part composition
- **Affected:** read_paper (untrusted content) combined with the population's existing connectors
- **Description:** For the requesting population (already connected: a document store and corporate email), this server adds continuous untrusted-content exposure — paper text enters model context — alongside existing private-data access and an email send channel.
- **Impact:** A crafted paper could instruct the agent to read document-store content and email it out. Not a defect in this server; a property of the combination.
- **Likelihood:** Moderate — requires a crafted paper to reach the agent, which is plausible for a research workflow.
- **Evidence:** `combined connected set (composition analysis)`
  ```
  read_paper -> untrusted content leg; existing document store -> private-data leg; existing email -> external-comms leg. All three legs present for the population.
  ```
- **Remediation:** Break a leg for the pilot: require confirmation on email-send after read_paper has fired, or scope the pilot to users without the email connector. Prefer a deterministic gateway control over relying on the model. (AGT-1, AGT-3)
- **Status:** open

### Finding-02 — Cross-registry name collision invites a supply-chain swap  ·  HIGH  ·  _reasoned_
- **Category:** Supply Chain · Part A
- **Affected:** package name (PyPI vs npm)
- **Description:** An unrelated third-party npm package exists under the same name. The project itself warns that installs must use `uv tool install` from PyPI, not npm/npx.
- **Impact:** A user who 'npm installs' this name gets someone else's code — a straightforward supply-chain substitution.
- **Likelihood:** Moderate — easy to hit by habit; the correct install path is non-obvious.
- **Evidence:** `npm registry vs PyPI`
  ```
  Same name resolves to an unrelated npm package; upstream README warns: install via `uv tool install` from PyPI only.
  ```
- **Remediation:** Managed install only: publish the pinned PyPI version internally and block ad-hoc npm/npx installs of this name. (SUP-1)
- **Status:** open

## Technical assessment
- **Purpose:** Bridges AI assistants to arXiv: search, download, and read paper content into model context, with local caching.
- **Creator Publisher:** Individual maintainer (blazickjp), ~400 stars
- **Maintenance Signals:** Active in 2026; single primary maintainer.
- **License:** Open source (verify current file at pin time)

| Tool | Function | Class |
|---|---|---|
| `search_papers` | Query arXiv by keyword, author, or category | read |
| `download_paper` | Fetch a paper (HTML/PDF) to the local cache | write |
| `list_papers` | List locally cached papers | read |
| `read_paper` | Load cached paper text into model context | read |

- **Auth Client To Server:** none
- **Auth Downstream:** anonymous public arXiv API
- **Token Passthrough:** False
- **Stored Credential Risk:** low
- **Notes:** No credentials exist to steal; host compromise yields only cached public papers.

## Risk rating
| Factor | Score |
|---|---|
| Provenance | 3 |
| Capability | 2 |
| Permissions | 1 |
| Hosting Exposure | 2 |
| Auth Strength | 2 |
| Credential Storage | 1 |
| Install Vector | 3 |
| Code Hygiene | 2 |
| **Composite** | **1.85** |

Overrides: Composition completes the trifecta for this population -> HIGH floor for that population absent conditions

## Limitations & disclaimer
Point-in-time static assessment (code review) of the package at pin time. Not a warranty. Findings require independent verification before remediation decisions rely on them.

Findings are marked `reasoned` (static review); none were reproduced with a live proof-of-concept. The composition finding depends on the combined connected set. Run the validator skill to confirm.

Checks not performed (coverage gaps): sandbox-egress-verification.
