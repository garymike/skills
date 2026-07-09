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

## Rating map

| Composite | Rating |
|---|---|
| ≤ 1.8 | LOW |
| 1.9 - 2.9 | MODERATE |
| 3.0 - 3.9 | HIGH |
| ≥ 4.0 | CRITICAL |

## Overrides (apply after arithmetic)

- Any automatic disqualifier from `risk-tiering.md` (hardcoded secrets, token passthrough, poisoned descriptions, typosquat, fetch-and-execute installs) → CRITICAL, recommendation `do_not_connect`.
- Known exploited CVE in the pinned version → CRITICAL until patched version reassessed.
- Composition: completes the lethal trifecta for a real user population → minimum HIGH regardless of composite, with the condition set that would reduce it stated in recommendations.
- Two or more High findings → minimum HIGH.

## Recommendation mapping

LOW → `connect`. MODERATE → `connect_with_conditions` (name them). HIGH → `connect_with_conditions` only if conditions demonstrably reduce the driving factors, else `do_not_connect`. CRITICAL → `do_not_connect` (or `reassess` when a specific fix, e.g. patched version, is pending).

Show the factor table and arithmetic in every report; a risk rating no one can challenge is a risk rating no one trusts.
