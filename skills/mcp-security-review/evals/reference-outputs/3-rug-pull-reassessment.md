# Re-assessment: ticketing MCP connector (definition hash changed)

A definition-hash change is a formal re-assessment trigger and, until proven otherwise, a potential rug pull. A changelog saying "minor improvements" is a claim, not evidence; the reviewed-vs-current diff is the evidence.

## Process

1. **Hold state.** Tier 2: reviewer discretion; keep the connector live but block the update from propagating (pinned version stays pinned; gateway continues enforcing the previously approved tool set) until the diff is reviewed. If current definitions cannot be obtained, or the vendor pushed the change server-side so the old set is already gone, treat as suspicious and suspend via gateway/credential disable. Measure time-to-suspend; this is the drill.
2. **Obtain and diff.** Pull the current tools/list, canonicalize, hash, and diff against the definitions recorded at the 4-month-old assessment. Classify every delta: new tool, removed tool, description wording change, schema change, annotation change.
3. **Scoped re-review.** Clean diff (e.g. typo fixes, added optional pagination param): fast pass — Part B human read of changed text only, plus composition delta (does any new/changed tool alter the trifecta math or shadow another server?). Suspicious diff (new instruction-like language, new parameters soliciting content, annotation flips, scope expansion): full Part B/D re-inspection and vendor questions before unblocking.
4. **Update the record.** Amend the decision record/report: new definition hash, diff summary, whether the overall risk rating changed, and reviewer sign-off. Register entry gets the new hash and next re-review date. If rating worsened, conditions are re-derived, not inherited.
5. **Close the loop.** If clean: unpin to the new version, re-pin, done. If rug pull confirmed: suspend, offboard per the lifecycle, preserve hashes and gateway logs for the incident record, and notify users with the alternative.

## Updated report delta (what changes in the document)

Header: new date, new definition hash. Findings: any diff-derived findings. Capabilities: inventory delta noted. Risk computation: re-scored only if factors moved. Machine block: `definition_hash_sha256`, `assessed_date`, and `overall_risk` updated; `recommendation` reaffirmed or changed.
