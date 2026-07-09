# Decision Record: <server name>

**Requester:** | **Reviewer:** | **Approver:** (ideally not the requester) | **Date:** | **Tier:**

## Summary

- Server, publisher, exact source and pinned version / endpoint:
- Deployment type and user population:
- Business purpose (one sentence):

## Findings

| Phase | Result | Notes (one line per checked item group) |
|---|---|---|
| Provenance & integrity (Part A) | pass/fail | |
| Tool surface (Part B) | pass/fail | |
| Code & runtime (Part C) | pass/fail/N-A | |
| Auth & data flow (Part D) | pass/fail/N-A | |
| Composition (trifecta, shadowing, flows, aggregate) | pass/conditions/fail | |

Tool-definition hash (SHA-256): `...`
Blast radius statement: ...

## Decision

**APPROVE / APPROVE WITH CONDITIONS / DENY**

Conditions (each is a control; unmet = denied):
1. e.g. Scopes reduced to X and Y; Z removed.
2. e.g. Gateway policy: block tool T when session has invoked server S.
3. e.g. Pilot limited to <group> for 60 days before expansion review.

Denial reasoning and viable alternatives (including first-party build via secure-mcp-builder):

## Lifecycle

- Register entry ID:
- Monitoring wired (what alerts, where):
- Re-review triggers: version change, tool-definition hash change, publisher change, scope change, security incident, or <cadence per tier> — whichever first.
- Offboarding owner:

**Approver sign-off:** ______________
