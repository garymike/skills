# Computed Risk Model

Reproducible, challengeable scoring. Eight factors, 1-5 each (5 = worst), weighted sum to a 1-5 composite, mapped to a rating. Findings override arithmetic: any Critical finding forces CRITICAL; two or more High findings force at least HIGH. Unknowns score 4 on their factor, never lower; ignorance is risk.

## Factors and weights

| Factor | Weight | 1 (best) | 3 | 5 (worst) |
|---|---|---|---|---|
| Provenance & maintenance | 0.10 | Established vendor, signed releases, active team | Known OSS, single active maintainer | Unknown individual, stale, unsigned |
| Capability / blast radius | 0.20 | Read-only, narrow | Writes to low-impact systems | Destructive, financial, external comms, code execution |
| Permissions requested | 0.15 | Minimal, mapped to purpose | Some excess read scope | Broad write scopes, admin, unmapped excess |
| Hosting exposure | 0.10 | Local stdio sandboxed | Remote managed, reputable | Local with host access, or remote self-hosted unhardened |
| Auth strength | 0.15 | OAuth 2.1 + PKCE, audience-validated | Scoped static API key | Weak/none, or any passthrough (auto-Critical) |
| Stored credential risk | 0.15 | Vault/keychain, rotated, revocable | Env vars, manual rotation | Plaintext files/config, no revocation path |
| Installation vector | 0.05 | No install (remote) or signed package | Registry package, pinned | Curl-pipe-sh, unsigned binary, marketplace one-click with scripts |
| Code hygiene & inspection results | 0.10 | Clean scan + clean human read | Minor findings, sane structure | Obfuscation, dynamic code loading, failed scan, uninspectable |

Composite = Σ(score × weight).

### `ema_status` and the Auth strength factor

All four values have a defined treatment; record which one applied.

- `verified_correct` does not raise the Auth strength score above the existing best tier (OAuth 2.1 + PKCE, audience-validated already scores 1): EMA is a centralized-policy enhancement on that same base, not a different mechanism. Record it instead as a positive differentiator in the report's posture paragraph, the same "positive signal, not required" treatment `inspection-checklist.md` Part E already gives published tool-definition manifests and signed releases.
- `verified_broken` scores Auth strength 5, whatever the underlying client-to-server mechanism looks like on its own. A bypassable authorization path is the effective authorization path, so OAuth 2.1 + PKCE underneath does not earn its usual 1 here. Same reasoning the factor table already applies to token passthrough, which also scores 5 regardless of the surrounding flow.
- `declared_unverified` raises Auth strength to at least 4, the standard unknown treatment from the opening rule. No exemption: the declaration itself is what a deploying organization relies on, so an unrun check on it is exactly the kind of ignorance that scores 4. If the mechanism already scores worse, keep the worse score; unknowns raise risk, never lower it.
- `not_declared` is neutral and has no effect on any factor. The server is simply not using the extension; score Auth strength on its client-to-server mechanism alone.

### `handle_security` and the Auth strength factor

- `verified_broken` scores Auth strength 5. A bypassable handle is a bypassable authorization path, scored the same way `ema_status: verified_broken` and token passthrough already are.
- `unverified` raises Auth strength to at least 4, the standard unknown treatment. Keep a worse score if the mechanism already earns one.
- `verified_sound` does not lower Auth strength below what the client-to-server mechanism earns on its own; sound handles are the baseline expectation under the stateless core, not a bonus.
- `not_applicable` is neutral and affects nothing.

### `tasks_status` and the Capability factor

Tasks scores through Capability / blast radius, not Auth strength, and carries no override: unbounded task creation is an availability problem, not a confidentiality or integrity bypass.

- `verified_unbounded` raises Capability by one step (never above 5). A cheap request that commits durable, uncancellable server-side work is real blast radius, but denial of service alone does not justify forcing a verdict. Note this is a relative step, not the "raise to at least 4" floor every other unknown and negative state uses. That is deliberate: Capability is already scored from the tool surface, and unbounded tasks *add* reach on top of whatever the tools provide rather than defining it. A floor would score a read-only server with sloppy task limits the same as a destructive one, which is the wrong answer.
- `declared_unverified` raises Capability to at least 4, the standard unknown treatment.
- `verified_bounded` and `not_declared` are neutral.

### `mcp_apps_status` and the Capability factor

- `reviewed_unsafe` forces CRITICAL by override, so its factor contribution is moot; still record Capability honestly for the register.
- `declared_unreviewed` raises Capability to at least 4: an unread UI resource is exactly the kind of unknown that scores 4, and it is the half of the MCP Apps surface the definition hash cannot see.
- `reviewed_safe` and `not_declared` are neutral.

## Rating map

| Composite | Rating |
|---|---|
| ≤ 1.8 | LOW |
| above 1.8, below 3.0 | MODERATE |
| 3.0 up to below 4.0 | HIGH |
| ≥ 4.0 | CRITICAL |

The bands are contiguous on purpose: every composite lands in exactly one. An earlier
version read `1.9 - 2.9` and `3.0 - 3.9`, which left 1.81 to 1.89 and 2.91 to 2.99
unclassifiable. That was not hypothetical, since a composite of 1.85 falls in the first
gap. Do not restate the bands as bare ranges without checking that the edges still meet.

## Overrides (apply after arithmetic)

- Any automatic disqualifier from `risk-tiering.md` (hardcoded secrets, token passthrough, poisoned descriptions, typosquat, fetch-and-execute installs) → CRITICAL, recommendation `do_not_connect`.
- `ema_status: verified_broken` → CRITICAL, recommendation `do_not_connect`. A server that advertises Enterprise-Managed Authorization while accepting a forged, wrong-`resource`, wrong-`aud`, or expired ID-JAG is a worse posture than not declaring the extension at all: it creates false assurance that centralized enterprise policy is enforced.
- `mcp_apps_status: reviewed_unsafe` → CRITICAL, recommendation `do_not_connect`. An MCP App renders inside the conversation, can push context updates to the model, and runs whatever its CSP admits. A UI that builds HTML from tool output, or whose `csp` admits origins the publisher does not control, is both a script-execution vector and an injection path into the conversation, wearing the host's own trust.
- `handle_security: verified_broken` → CRITICAL, recommendation `do_not_connect`. Under the stateless core the handle is the only thing binding a caller to their own work. A predictable or unbound handle means another caller can resume, read, or cancel it, which is a direct authorization bypass, not a hardening gap.
- Known exploited CVE in the pinned version → CRITICAL until patched version reassessed.
- Composition: completes the lethal trifecta for a real user population → minimum HIGH regardless of composite, with the condition set that would reduce it stated in recommendations.
- Two or more High findings → minimum HIGH.

## Recommendation mapping

LOW → `connect`. MODERATE → `connect_with_conditions` (name them). HIGH → `connect_with_conditions` only if conditions demonstrably reduce the driving factors, else `do_not_connect`. CRITICAL → `do_not_connect` (or `reassess` when a specific fix, e.g. patched version, is pending).

Show the factor table and arithmetic in every report; a risk rating no one can challenge is a risk rating no one trusts.
