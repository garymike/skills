# Composition Analysis

Evaluate the state the org will be in AFTER approval, not the server in isolation. The unit of risk is the connected set per user population. Attack success climbs steeply with connected-server count, so each approval changes the risk of every prior one.

## 1. Trifecta completion check

The lethal trifecta (Simon Willison's term) is the dangerous combination of private-data access, exposure to untrusted content, and an external communication channel. Build the combined capability table for each affected user population:

| Leg | Provided by (existing) | Added by candidate? |
|---|---|---|
| Access to private data | | |
| Exposure to untrusted content | | |
| External communication channel | | |

If the candidate completes the trifecta (adds the missing leg to an existing pair), that is a Tier 3 fact regardless of the server's own tier. Options, in order of preference: deny; approve only for a population that lacks the other legs; approve with a gateway policy that breaks the chain (e.g. block the exfil-capable tool once the session has touched the private-data server); approve with human-in-the-loop on the completing tools. Record which option, and why.

Watch the subtle legs: URL-fetching tools are external comms (query-string exfiltration); write-back into shared systems (comments, tickets, calendar invites, filenames) is external comms; any tool that renders or summarizes third-party content (web, email, docs, tickets) is untrusted-content exposure.

## 2. Tool shadowing and cross-server influence

- Name collisions: does any candidate tool name collide or near-collide with an already-connected tool? A collision lets a malicious server intercept calls meant for a trusted one; a near-collision confuses the model into the wrong pick.
- Cross-references: do any candidate descriptions mention other tools, other servers, or how the agent should treat other results? A description should describe its own tool only — anything else is shadowing behavior, and disqualifying.
- Priority/urgency language ("always use this tool first", "before any other tool") biases selection across the whole toolset; disqualifying.

## 3. Cross-server data flow

Trace realistic chains: data read via server A becomes a parameter to server B. Which chains does the candidate make possible, and which are dangerous (confidential data into a tool that leaves the org)? Gateways can monitor for known-sensitive patterns crossing servers; note what monitoring is feasible in the decision record.

## 4. Aggregate scope review

Sum the credentials and scopes the user population holds across all connected servers after approval. Individually reasonable scopes can aggregate into "this population's agent can read email, files, and CRM, and can send email and post publicly" — a different risk conversation than any single approval. If the aggregate crosses a threshold the org has not consciously accepted, escalate before approving.

## 5. Blast radius statement

One paragraph in the decision record: if this server turns malicious tomorrow (rug pull) or its vendor is breached, what can it reach, through whom, and how would we find out? If the honest answer is "everything the pilot population can touch, and we would not notice," fix the monitoring before approving, not after.
