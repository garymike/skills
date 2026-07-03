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

```bash
gh api repos/<owner>/<repo>/actions/permissions/workflow -X PUT \
  -f default_workflow_permissions=read \
  -f can_approve_pull_request_reviews=false
```

### Check for unpinned actions in workflows (free)

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

CodeQL supports: `cpp`, `csharp`, `go`, `java`, `javascript`, `python`, `ruby`, `swift`.

### Gitleaks secret scanning (free — for private repos)

**Fail-hard (recommended):**
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

**Warn-only** — add `continue-on-error: true` to the gitleaks step.

Use the GitHub MCP `create_or_update_file` tool to push this without cloning locally.

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

Returns 403 for private repos on Free plan — do not attempt.

### Add SECURITY.md (free, all repos)

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

Inspect matches — `.env.example` is fine, `.env` is not.

### Archive a stale repo

```bash
gh api repos/<owner>/<repo> -X PATCH -f archived=true
```

### Delete a repo (requires delete_repo scope)

```bash
gh auth refresh -h github.com -s delete_repo
gh repo delete <owner>/<repo> --yes
```

---

## Gotchas

- `hasVulnerabilityAlertsEnabled` is not a valid `--json` field in `gh repo list` — use the API endpoint instead
- Branch protection returns **403** (not 404) for private repos on Free plan
- Secret scanning returns **422** when enabled on private repos without GHAS — offer gitleaks instead
- Push protection returns **422** on private repos without GHAS — same as above
- `gh repo delete` requires the `delete_repo` scope — default login token won't have it
- The vulnerability-alerts API returns 404 when disabled (not a 200 with a `false` field)
- Gitleaks `fetch-depth: 0` is required — without it only the latest commit is scanned
