# MCP Security Assessment — analytics-mcp
**DO NOT CONNECT** · **CRITICAL RISK** (2.4)

## Executive summary
1 Critical · 1 High · 1 Moderate · 0 Low · 0 Info

analytics-mcp is a sound read-only warehouse connector with one unsafe addition. Its new MCP App renders in the conversation under the host's own trust, yet it admits scripts from a public CDN the team does not control, writes the server's own tool output into innerHTML, and asks for camera access it has no use for. Any one of those turns an interactive chart into script execution and a path to push attacker-chosen context at the model. The rest of the server is fine, which is exactly why the UI needs fixing rather than the connector being abandoned.

**Top findings**
- **CRITICAL** MCP App CSP admits a public CDN, permitting third-party script execution in the UI (Finding-01)
- **HIGH** MCP App writes tool output into innerHTML (Finding-02)

**Scope:** Review analytics-mcp before a company-wide rollout, with attention to the new MCP App shipped by analytics_render_dashboard.

_Standard review · modes code · 2026-07-27 · checks not performed: 2_

## Recommendations
1. Bundle the chart library into the UI and empty csp.resourceDomains, so the app executes only script the team ships and reviews. (findings Finding-01 · UI-1)
2. Replace the innerHTML assignment with textContent, and keep UI markup independent of runtime data. (findings Finding-02 · UI-1, OUT-3)
3. Drop the camera permission from the UI resource. (findings Finding-03 · UI-1, AGT-4)
4. Record a hash of the ui:// resource content alongside the tool-definition hash, and re-check it on every version bump. The definition hash covers only the resourceUri pointer, so CSP and markup can change beneath an unchanged pointer. (findings Finding-01, Finding-02 · SUP-6)

## Findings

### Finding-01 — MCP App CSP admits a public CDN, permitting third-party script execution in the UI  ·  CRITICAL  ·  _reasoned_
- **Category:** Supply Chain / Untrusted Content · Part B · UI-1
- **Affected:** ui://analytics/dashboard.html (resource _meta.ui.csp)
- **Description:** The UI resource declares csp.resourceDomains of https://cdn.jsdelivr.net. resourceDomains governs scripts, stylesheets, images, and fonts, and the host renders MCP Apps in a deny-by-default iframe, so this entry is the specific thing permitting third-party script execution. jsdelivr is a public CDN serving arbitrary published packages; the Data Platform team does not control what it serves.
- **Impact:** Anyone able to publish or tamper with content at that origin executes script inside a UI the user sees as part of the assistant. Because an MCP App can call tools and push context updates to the model, that script is not confined to browser mischief: it can drive tool calls the user believes they authorized and inject attacker-chosen text into the conversation, wearing the host's trust the whole time.
- **Likelihood:** Moderate: it needs a compromised or malicious package at the CDN origin rather than a direct attack on this server, but that is a well-worn supply-chain path and nothing in this configuration would detect it.
- **Evidence:** `resource read handler for ui://analytics/dashboard.html`
  ```
  _meta: { ui: { csp: { connectDomains: ["https://api.analytics-vendor.example"], resourceDomains: ["https://cdn.jsdelivr.net"] }, domain: "analytics.acme.internal" } }
  ```
- **Remediation:** Bundle the chart library into the HTML (vite-plugin-singlefile or equivalent) and drop resourceDomains to empty, which is the configuration the extension is designed around. If an external origin is genuinely unavoidable, it must be one the team controls and pins by digest, never a shared public CDN. (UI-1, SUP-1)
- **Status:** open

### Finding-02 — MCP App writes tool output into innerHTML  ·  HIGH  ·  _reasoned_
- **Category:** Injection · Part B · UI-1, OUT-3
- **Affected:** ui://analytics/dashboard.html (rendering code)
- **Description:** The UI assigns the tool's own result into innerHTML: document.getElementById('title').innerHTML = result.dashboardName. Dashboard names come from the warehouse, so any user who can name a dashboard controls markup rendered inside the app.
- **Impact:** A dashboard named with a script payload executes when the app renders, in the same trusted UI context as F-01 and with the same reach into tool calls and model context. This is the case UI-1 and OUT-3 both exist to prevent: UI markup built from runtime data rather than shipped as a reviewed static artifact.
- **Likelihood:** High where dashboard names are user-editable, which is the normal case for a warehouse analytics tool.
- **Evidence:** `ui://analytics/dashboard.html`
  ```
  document.getElementById('title').innerHTML = result.dashboardName;
  ```
- **Remediation:** Use textContent rather than innerHTML for any value derived from tool output or warehouse data. Keep the UI a static reviewed artifact whose markup does not vary with runtime data. (UI-1, OUT-3)
- **Status:** open

### Finding-03 — MCP App requests camera permission unrelated to its function  ·  MODERATE  ·  _reasoned_
- **Category:** Excessive Agency · Part B · UI-1, AGT-4
- **Affected:** ui://analytics/dashboard.html (resource _meta.ui permissions)
- **Description:** The UI resource requests camera permission. Rendering a chart from data the tool already returned needs no camera access, and nothing else in the tool's description suggests a capture feature.
- **Impact:** Excess capability in a UI that already has two paths to script execution. If either is exploited, the granted permission is available to the attacker; and a permission prompt arriving from a trusted assistant surface is one users are unusually likely to accept.
- **Remediation:** Remove the camera permission. Request only capabilities the tool's stated function requires, and justify each in the tool description. (UI-1, AGT-4)
- **Status:** open

## Technical assessment
- **Purpose:** Query the analytics warehouse and render dashboards for agents, company-wide.
- **Publisher:** first-party (Data Platform)
- **Maintenance:** Active internal repo, fortnightly releases, 4 maintainers.
- **License:** internal

| Tool | Function | Class |
|---|---|---|
| `analytics_query` | Run a read-only query against the warehouse. | read |
| `analytics_list_dashboards` | List dashboards visible to the caller. | read |
| `analytics_render_dashboard` | Render a dashboard as an interactive MCP App. | read |

**Permissions**
- warehouse.read (scoped to the caller's own row-level grants)

**Hosting**
- **Hosting model:** remote self
- **Install methods:** Internal service catalog; clients connect to https://mcp.analytics.acme.internal
- **Install-time behavior:** No install; remote HTTP endpoint.
- **Data residency:** Company-owned infrastructure, same region as the warehouse.

**Protocols**
- **MCP spec version:** 2026-07-28
- **Transport:** streamable-http
- **Forward-compat notes:** Stateless core; no session-derived security decisions observed.
- **Tasks status:** not_declared
- **MCP Apps status:** reviewed_unsafe

**Authentication & credential risk**
- **Client auth:** oauth21_pkce
- **Downstream auth:** Service identity with per-caller row-level grants enforced in the warehouse.
- **Token passthrough:** No
- **Handle security:** not_applicable
- **Credential risk:** low
- **Notes:** Client auth and downstream scoping are sound and are not the reason for this verdict. The server declares no cross-call handle surface: it exposes no Tasks extension and threads no opaque handles between calls, so handle_security is not_applicable rather than unverified.

## Risk rating
| Factor | Score |
|---|---|
| Provenance | 3 |
| Capability | 4 |
| Permissions | 2 |
| Hosting Exposure | 2 |
| Auth Strength | 1 |
| Credential Storage | 2 |
| Install Vector | 1 |
| Code Hygiene | 3 |
| **Composite** | **2.4** |

Overrides: mcp_apps_status: reviewed_unsafe -> CRITICAL, recommendation do_not_connect

## Limitations & disclaimer
Point-in-time assessment (2026-07-27) against the reviewed commit. Static and source review only; the UI was read as shipped, not rendered and exercised in a host. This report is not a warranty.

All three findings are reasoned from source: the CSP and permissions were read from the resource read handler and the sink from the shipped HTML, none exploited. Rendering the app in a real host with a poisoned dashboard name would upgrade F-02 to confirmed.

Checks not performed (coverage gaps): part-e-runtime, sandbox.
