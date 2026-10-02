# GitHub Security Audit — Reference

## Free vs paid

| Feature | Free plan | Pro ($4/user/mo) | GHAS / Enterprise |
|---|---|---|---|
| Dependabot alerts | ✓ all repos | ✓ | ✓ |
| Dependabot auto-fix PRs | ✓ all repos | ✓ | ✓ |
| Secret scanning (public repos) | ✓ | ✓ | ✓ |
| Secret scanning (private repos) | ✗ use gitleaks | ✗ | ✓ |
| Push protection (public repos) | ✓ | ✓ | ✓ |
| Push protection (private repos) | ✗ | ✗ | ✓ |
| CodeQL analysis (public repos) | ✓ | ✓ | ✓ |
| CodeQL analysis (private repos) | ✗ | ✗ | ✓ |
| Branch protection (public repos) | ✓ | ✓ | ✓ |
| Branch protection (private repos) | ✗ | ✓ | ✓ |
| Signed commits enforcement | ✓ public | ✓ | ✓ |
| Delete-branch-on-merge | ✓ all repos | ✓ | ✓ |
| GitHub Actions (gitleaks workflow) | ✓ 2,000 min/mo private | ✓ | ✓ |
| SECURITY.md | ✓ all repos | ✓ | ✓ |
| Private vulnerability reporting | ✓ public repos | ✓ | ✓ |

**Never enable a paid feature without confirming with the user first.**

---

## Fix commands

### Dependabot alerts + auto-fix (free, all repos)

```bash
for repo in <repo1> <repo2>; do
  gh api repos/<owner>/$repo/vulnerability-alerts -X PUT
  gh api repos/<owner>/$repo/automated-security-fixes -X PUT
done
```

### Delete-branch-on-merge (free, all repos)

```bash
gh api repos/<owner>/<repo> -X PATCH -f delete_branch_on_merge=true --jq '.delete_branch_on_merge'
```

### Actions default permissions — read-only (free, all repos)

Restricts all workflows to read-only by default. Individual workflows can still request write via `permissions:`.

```bash
gh api repos/<owner>/<repo>/actions/permissions/workflow -X PUT \
  -f default_workflow_permissions=read \
  -f can_approve_pull_request_reviews=false
```

Verify:
```bash
gh api repos/<owner>/<repo>/actions/permissions/workflow --jq '{default: .default_workflow_permissions, can_approve_prs: .can_approve_pull_request_reviews}'
```

### Check for unpinned actions in workflows (free)

Scan workflow files for `uses: owner/action@v1` style tags (unpinned). SHA-pinned looks like `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683`.

```bash
gh api repos/<owner>/<repo>/git/trees/main?recursive=1 \
  --jq '[.tree[] | select(.path | startswith(".github/workflows/")) | .path]'
# Then read each file and grep for @v or @main/@master (unpinned)
```

Flag any `@v`, `@main`, or `@master` references. SHA pins are 40-char hex hashes.

### Enable push protection (free on public repos)

```bash
gh api repos/<owner>/<repo> -X PATCH \
  -f "security_and_analysis[secret_scanning_push_protection][status]=enabled"
```

Note: returns 422 on private repos without GHAS — do not attempt on private repos.

### Enable CodeQL (free on public repos)

Commit `.github/workflows/codeql.yml`:

```yaml
name: CodeQL analysis

on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 8 * * 1'

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      actions: read
      contents: read
    strategy:
      matrix:
        language: [javascript, python]  # adjust to repo languages
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
```

Adjust the `language` matrix to match the repo's primary languages. The built-in set is `actions`, `cpp`, `csharp`, `go`, `java`, `javascript`, `python`, `ruby`, `rust`, `swift` — with `typescript` → `javascript`, `kotlin` → `java`, and `c`/`c++` → `cpp` as aliases.

**Check the repo's languages before adding this workflow.** `Shell`, `PowerShell`, `Bicep`, and `Dockerfile` are not CodeQL languages, and a matrix naming one analyses nothing. For an infra repo with no supported language, `actions` alone is still worth running — it inspects the workflow files for script injection, excessive permissions, and untrusted-input flows. Verify the current set against `github/codeql-action` → `src/languages/builtin.json` rather than trusting this list.

```bash
gh api repos/<owner>/<repo>/languages --jq 'keys|join(", ")'
```

### Gitleaks secret scanning (free — for private repos)

When prompting user for fail-hard vs warn-only, present both options:

**Fail-hard (recommended)** — blocks the PR/push if secrets found:
```yaml
name: Secret scanning

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Warn-only** — reports findings but does not block merges:
```yaml
name: Secret scanning

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        continue-on-error: true
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Use the GitHub MCP `create_or_update_file` tool to push this without cloning. Push to all private repos in parallel.

### Branch protection (public repos — free)

```bash
gh api repos/<owner>/<repo>/branches/main/protection -X PUT \
  --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  },
  "required_signatures": true,
  "restrictions": null
}
EOF
```

`required_signatures: true` enforces GPG/SSH signed commits. Note: returns 403 for private repos on Free plan — do not attempt.

Commits created through the **contents API are unsigned**, so on a repo requiring signatures they cannot be pushed to the protected branch. A side-branch PR does not rescue them either: GitHub signs the merge commit it writes, but the branch's own commits stay unsigned and the PR is refused with `the base branch policy prohibits the merge` — green checks or not. Use the GraphQL `createCommitOnBranch` mutation instead, which GitHub signs server-side. See [landing signed commits from automation](#landing-signed-commits-from-automation).

### Add SECURITY.md (free, all repos)

Minimal template to commit at `SECURITY.md` in the repo root:

```markdown
# Security Policy

## Reporting a vulnerability

Please do not open a public issue for security vulnerabilities.

Use GitHub's private vulnerability reporting:
https://github.com/<owner>/<repo>/security/advisories/new

We will acknowledge receipt within 48 hours and aim to resolve critical issues within 14 days.
```

### Enable private vulnerability reporting (free, public repos)

```bash
gh api repos/<owner>/<repo>/private-vulnerability-reporting -X PUT
```

### Scan for sensitive files in public repos

```bash
gh api repos/<owner>/<repo>/git/trees/main?recursive=1 \
  --jq '[.tree[] | select(.path | test("[.](env|pem|key|crt|p12|pfx)$")) | .path]'
```

Inspect any matches before flagging — `.env.example` is fine, `.env` is not. Source files whose names merely contain `credential` are usually legitimate code, not secrets; open them before reporting.

### Archive a stale repo

```bash
gh api repos/<owner>/<repo> -X PATCH -f archived=true
```

### Delete a repo (requires delete_repo scope)

```bash
gh auth refresh -h github.com -s delete_repo   # one-time scope grant
gh repo delete <owner>/<repo> --yes
```

---

## Workflow run health

A repo can have `security.yml` and still scan nothing. Check the last run of **each trigger**, not the newest run overall.

### 1. Per-trigger status

```bash
for r in <owner>/<repo1> <owner>/<repo2>; do
  echo "$r"
  echo "  push:     $(gh run list --repo $r --workflow Security --event push     --limit 1 --json conclusion --jq '.[0].conclusion // "none"')"
  echo "  schedule: $(gh run list --repo $r --workflow Security --event schedule --limit 1 --json conclusion --jq '.[0].conclusion // "none"')"
done
```

A green `push` next to a failing `schedule` is the signal to chase — the `audit` job is gated on `if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'`, so it never runs on push or PR.

`schedule: none` on a repo that has had `security.yml` for over a week usually means the default branch is wrong: scheduled runs resolve against the default branch, so a workflow living only on `main` never fires if the default branch points elsewhere.

### 2. Diagnose a `startup_failure`

There are no logs, no jobs, and no annotations, so nothing is retrievable through the usual routes. Diagnose by inspection:

```bash
# Does the pinned reusable workflow request a permission the caller withheld?
gh api "repos/<owner>/security-workflows/contents/.github/workflows/security-scan.yml?ref=<PINNED_SHA>" \
  --jq '.content' | base64 -d | sed -n '/^jobs:/,/steps:/p'
```

Compare the reusable workflow's job-level `permissions:` against the caller's. Every permission the callee requests must also appear in the caller — the caller's block is a hard ceiling, and any gap is rejected before a job starts. `packages: read` is the usual culprit, added when a workflow starts pulling an image from GHCR.

### 3. Diagnose a failing job step

```bash
JID=$(gh api repos/<owner>/<repo>/actions/runs/<RUN_ID>/jobs \
  --jq '.jobs[]|select(.conclusion=="failure")|.id')
gh api repos/<owner>/<repo>/actions/jobs/$JID/logs --allow-escape-sequences \
  | sed 's/\x1b\[[0-9;]*m//g' | tail -40
```

Without `--allow-escape-sequences` the call errors out; without the `sed` the output is unreadable.

### 4. Compare pins across callers

```bash
for r in <repo list>; do
  c=$(gh api repos/$r/contents/.github/workflows/security.yml --jq '.content' 2>/dev/null | base64 -d 2>/dev/null)
  [ -z "$c" ] && { echo "$r | NO security.yml"; continue; }
  echo "$r | packages:read=$(echo "$c" | grep -c 'packages: read') | ref=$(echo "$c" | grep -oE 'security-scan\.yml@[^ ]+' | head -1 | sed 's/.*@//' | cut -c1-12)"
done
```

Then check whether an old pin predates a known fix in the shared workflow:

```bash
gh api "repos/<owner>/security-workflows/contents/.github/workflows/security-audit.yml?ref=<SHA>" \
  --jq '.content' | base64 -d | grep -m1 'PERMS=\$('
```

An advisory step that captures command output must use `|| true` — under `bash -e`, a failed command inside `VAR=$(...)` aborts the job even when the step only meant to emit a `::warning::`.

---

## Landing signed commits from automation

A branch requiring signed commits rejects anything `git commit` produces inside Actions, because `GITHUB_TOKEN` is not a signing key. This is not a one-off to force through: a weekly job that pushes a branch produces an unmergeable branch *every week*, which trains whoever is on the other end to treat `--admin` as routine in the repo that guards everything else.

GitHub's GraphQL `createCommitOnBranch` signs server-side. Same token, same `contents: write`, no bot signing key to store or rotate, and the result comes back `Verified` and mergeable with no bypass.

The branch must already exist and `expectedHeadOid` must match its current tip, so reset the ref first to replicate a force-push:

```bash
gh api repos/<owner>/<repo>/git/refs/heads/<branch> -X PATCH -f sha=$BASE -F force=true
```

Then commit:

```bash
gh api graphql --input payload.json --jq '.data.createCommitOnBranch.commit.signature'
```

`payload.json` holds the query plus `variables.input` with `branch` (`repositoryNameWithOwner` + `branchName`), `expectedHeadOid`, `message` (`headline` + `body`), and `fileChanges.additions[]` as `{path, contents}` with contents base64-encoded. Deletions go in `fileChanges.deletions[]` as `{path}`. The mutation body:

```graphql
mutation($input: CreateCommitOnBranchInput!) {
  createCommitOnBranch(input: $input) { commit { oid signature { isValid state } } }
}
```

**Always assert the result.** Require `signature.state == "VALID"` and fail otherwise. An unsigned commit cannot merge, and the failure stays invisible until someone tries weeks later.

To prove two branches carry identical content, compare `.commit.tree.sha` — the commit SHAs differ, a three-dot compare still lists every file, but matching trees are conclusive.

## Dependabot alert reality checks

The alert list is the least trustworthy part of a Dependabot setup. Four mechanisms make it understate exposure, and all four have been hit in this estate. **Never report a repo clean on a single `state=open` query.**

### 1. `state=open` is not the whole picture

Alerts live in four states: `open`, `fixed`, `dismissed`, `auto_dismissed`. A `state=open` query returns zero while `auto_dismissed` holds real, unpatched, high-severity advisories — and the default GitHub alerts view hides them too.

```bash
for st in open auto_dismissed dismissed; do
  echo "  $st => $(gh api "repos/<owner>/<repo>/dependabot/alerts?state=$st&per_page=100" --jq 'length')"
done
```

Treat `dismissed` as a deliberate human decision and leave it alone (read `dismissed_reason`). Treat `auto_dismissed` as a finding until proven otherwise.

### 2. The auto-triage rule's premise is wrong for bundled frontends

GitHub's default auto-triage rule, *dismiss low impact issues for development dependencies*, closes anything at `scope=development`. Its premise is that a dev dependency never reaches production. **That is false for any bundled frontend.** In a SvelteKit, Next.js, Vite or Tauri project the build output ships to users, and the packages that produced it contribute runtime code to that bundle. npm's `devDependency` means build-time *installation*, not absence from the shipped artifact.

A **high**-severity `nanoid` advisory sat auto-dismissed for seven weeks in a SvelteKit + Tauri desktop app on `adapter-static`, alongside `@sveltejs/kit` and `devalue` — the last being SvelteKit's serialization library, which executes in the webview at runtime.

Read `.dependency.scope` on each auto-dismissed alert, then judge against the project's shape rather than the label. There is **no REST API** for auto-triage rules: disabling one is a manual change under Settings → Advanced Security → Dependabot alerts → auto-triage rules, so hand it to the user. Check it per repo — turning it off on one leaves the rest armed.

### 3. A failing updater suppresses alert *creation*

The worst of the four, because the list stays authoritative-looking while it lies. `Dependabot Updates` failing does not merely stop PRs being opened — it stops alerts being created. A single advisory the resolver cannot compute exits the run non-zero and starves the whole cycle.

Observed: a repo displayed **8** open advisories all day. The moment one merge gave the updater a clean rescan, **12 more appeared within seconds**, including a critical. True exposure was 20. That updater had been failing 15 of its last 30 runs for a month.

```bash
gh run list --repo <owner>/<repo> --workflow "Dependabot Updates" --limit 30 \
  --json conclusion --jq '[.[]|.conclusion]|group_by(.)|map("\(.[0]):\(length)")|join("  ")'
```

**A red updater invalidates the alert count.** Report it as a finding in its own right, and never record a repo clean on a count taken while its last updater run failed.

### 4. Merging the PR is not the same as clearing the advisory

A second copy of the package can sit elsewhere in the tree at a hard pin. `mailparser@3.9.23` pins `nodemailer` at exactly `10.0.1` — no caret — so bumping the declared `nodemailer` to 10.0.9 left the transitive copy inside both advisory ranges, and the alert count did not move at all.

Verify by reading the lockfile for resolved versions rather than trusting the merge:

```bash
gh api "repos/<owner>/<repo>/contents/pnpm-lock.yaml" --jq '.content' | base64 -d \
  | grep -E "^  (<pkg1>|<pkg2>)@"
```

### Fixing what Dependabot cannot

**Read the repo's own documented procedure first.** One monorepo records in `pnpm-workspace.yaml` that `pnpm.overrides` is inert in its build and that two historical pins were silently dead because of it. The working fix there is to update the **parent** package until the patched version resolves — which is also the general shape for a transitive advisory.

```bash
pnpm -r update <transitive-pkg> --lockfile-only                # parent's range already allows the fix
pnpm -C <workspace-pkg> update <parent-pkg> --lockfile-only    # parent pins it hard
npm update <pkg> --package-lock-only                           # npm equivalent
```

Check the parent's declared range before accepting that a fix is unreachable. Dependabot reported `security_update_not_possible` for undici with `latest-resolvable-version: 7.29.0` against a 7.29.1 floor; undici arrived only via `jsdom@29.1.1`, which declares `^7.25.0` and permits it. The diagnosis was simply wrong, and a plain re-resolution fixed it.

### Sequential lockfile merges can silently revert a fix

Several Dependabot PRs touching one lockfile were each generated against an older base. Merging them in quick succession lets a textual auto-merge overwrite a landed fix.

Observed: three npm PRs squash-merged within 14 seconds. The first reverted `adm-zip` to a vulnerable version, five alerts opened, and the later merges happened to restore it — the whole window lasting nine seconds and leaving only a stale notification email. Had the order differed, the revert would have stuck behind a green dashboard.

Merge one at a time and let Dependabot rebase between, or set `required_status_checks.strict=true` so a stale branch must update first. After any such sequence, re-read the lockfile for the expected versions **and** re-query the alerts — the window can open and close in seconds.

### Security updates run without a declared ecosystem; version updates do not

A `dependabot.yml` listing only `github-actions` still receives security PRs for npm or pip, because security updates need no ecosystem entry. Routine version updates do. The effect is that application dependencies never move until an advisory forces them, so every bump arrives as an emergency. Compare declared ecosystems against the manifests actually present and flag the gap.

---

## Gotchas

- `hasVulnerabilityAlertsEnabled` is not a valid `--json` field in `gh repo list` — use the API endpoint instead
- Branch protection returns **403** (not 404) for private repos on Free plan
- Secret scanning returns **422** when enabled on private repos without GHAS — offer gitleaks instead, never try to enable it on private repos
- Push protection returns **422** on private repos without GHAS — same as above
- `gh repo delete` requires the `delete_repo` scope — default login token won't have it
- The vulnerability-alerts API returns 404 when disabled (not a 200 with a `false` field) — treat 404 as "disabled"
- CodeQL `autobuild` works for compiled languages; interpreted languages (JS, Python) don't need it, and with `build-mode: none` the step should be omitted entirely
- Gitleaks `fetch-depth: 0` is required — without it only the latest commit is scanned, not the full history
- `startup_failure` yields no jobs, no logs, and no annotations — `gh run view --log` returns "log not found". Diagnose by inspecting the workflow files, not the run
- A reusable workflow cannot request a permission its caller withheld; the caller's `permissions:` block is a hard ceiling and the mismatch is rejected at startup
- Scheduled runs resolve against the **default branch** — a workflow on `main` never fires on a schedule if the default branch points at some other branch
- `gh run list --workflow` matches on the workflow's `name:` field, not the filename
- Reading Actions job logs needs `--allow-escape-sequences`; strip ANSI with `sed 's/\x1b\[[0-9;]*m//g'`
- CodeQL's built-in languages are `actions, cpp, csharp, go, java, javascript, python, ruby, rust, swift`. **Shell, PowerShell, Bicep, and Dockerfile are not among them** — do not add a CodeQL workflow for those and call it coverage. `actions` analyses workflow files themselves and is often the only applicable language for an infra repo. Verify against `github/codeql-action` → `src/languages/builtin.json` rather than assuming
- Dependabot rarely opens a PR for a **transitive** Rust dependency, even with security updates on. Check `Cargo.lock` for the vulnerable crate, confirm the parent's version requirement already allows the patched release, and fix with `cargo update -p <crate> --precise <version>` — a lockfile-only change
- **Force-resetting a PR branch to its base auto-closes the PR.** Pushing commits afterwards leaves them on the branch but the PR stays `CLOSED` and `gh pr checks` reports "no commit found on the pull request". Either reset and commit as one operation, or `gh pr reopen` after — and re-check the state rather than assuming the push reopened it
- **`gh api -f` sends every value as a string.** `-f strict=true` is rejected with `422 "true" is not a boolean`; use `-F strict=true` for real booleans and numbers
- **`core.autocrlf=true` plus the GitHub API will reflow an entire file.** Git converts LF to CRLF on checkout, but the contents API and `createCommitOnBranch` bypass git's smudge/clean filters, so committing the working-copy bytes rewrites every line of an LF-stored file. `git diff` hides this — it normalises, so it still shows a small diff. Compare the local bytes against the actual blob before committing: `gh api "repos/<o>/<r>/contents/<path>" --jq '.content' | base64 -d`, count `\r\n` in both, and normalise to match the blob
- **Check allowed merge methods before merging.** `gh pr merge --squash` fails with `Squash merges are not allowed on this repository`; read `allow_squash_merge`, `allow_merge_commit` and `allow_rebase_merge` from the repo API and pick one that is enabled
- **Required status checks can be empty on a repo with extensive CI.** `required_status_checks: null` while CodeQL, Semgrep, Checkov and tests all run means none of them gate a merge. Verify the checks are *configured*, not merely that the workflows exist
- When choosing which checks to require, prefer jobs with no path or event gating. A job skipped by an `if:` still creates a check run with conclusion `skipped`, which counts as passing; a workflow skipped by a top-level `paths:` filter never creates the check run at all and blocks the PR forever. Exclude anything conditional — a `needs: changes` test job can skip on an unrelated PR
