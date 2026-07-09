# Onboarding, Monitoring, Re-review, Offboarding

Approval starts the lifecycle. This file covers everything after "yes" and the path to "no longer".

## Onboarding

- **Pin everything**: exact version (local) with lockfile, or endpoint + declared capability set (remote); record the tool-definition SHA-256 from the review. Auto-update is disabled; updates re-enter review (fast re-review if the diff is clean).
- **Least-privilege connection**: create the credential/OAuth grant with exactly the approved scopes, per-server (never reuse a credential across servers), owned by a named identity, revocable unilaterally.
- **Sandbox local servers**: container or OS sandbox with your standard profile: restricted filesystem, explicit egress allowlist, non-root, no access to credential stores beyond its own env vars.
- **Gateway policy** (remote, Tier 2+): route through the MCP/API gateway; apply the conditions from the decision record (tool blocks, rate limits, DLP patterns).
- **Register**: inventory entry with owner, tier, hash, conditions, re-review date. Unregistered = shadow server = incident.
- **User notice**: tell the user population what was approved, with which conditions, and how to report weirdness.

## Continuous monitoring

Wire before first production use, proportional to tier:

- **Definition-change detection** (rug pull): re-hash the tool set on connection or on a schedule; hash mismatch alerts security and, for Tier 3, auto-suspends pending re-review. This is the single highest-value control in the file.
- **New-tool / removed-tool alerts**: any change to the tool inventory is an event.
- **Behavioral anomalies**: first-seen egress destinations (local), abnormal call frequency, calls to tools outside the approved purpose, instruction-like patterns appearing in tool responses.
- **Vulnerability watch**: the pinned package/version on the dependency watchlist; publisher advisories subscribed.
- **Cross-server flow monitoring** where the composition analysis flagged chains.

## Re-review triggers

Any of: version bump, tool-definition hash change, scope/permission change request, publisher or ownership change, relevant CVE or incident (theirs or the class), composition change (a new server added that alters this one's trifecta math), or the tier's calendar cadence. Re-review scope is the diff plus composition, not necessarily the full checklist; a clean minor-version diff with unchanged hashes is a fast pass.

## Suspension and offboarding

- **Suspend** (reversible, fast): gateway block or credential disable while investigating a trigger. Practice this path; measure time-to-suspend.
- **Offboard** (final): revoke tokens/keys, delete the grant, remove gateway rules and sandbox profiles, uninstall packages from managed hosts, close the register entry with a disposition note, and notify users with the alternative (if any). An approval with no living owner is offboarded by default at re-review time.

## Incident hook

If a connected server is implicated in an incident: suspend first, investigate second. Preserve the tool-definition hashes and gateway logs; the diff between reviewed and current definitions is often the whole story.
