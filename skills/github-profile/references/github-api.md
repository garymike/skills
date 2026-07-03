# Deploying via the GitHub API

How to create and update the special `<username>/<username>` repo. The safe path
is wrapped by `scripts/deploy_profile.py`; this file explains what it does and
the manual equivalents.

## Ground rules

- **Confirm before anything becomes public.** Repo creation, commits, and pushes
  all publish to the user's account. Show the final README and get an explicit
  "yes, publish" before pushing. Ask again for each subsequent push; one
  approval does not cover future edits.
- **Never handle tokens in chat.** Authenticate with `gh auth login` or rely on
  a token already present in the environment (`GH_TOKEN` / `GITHUB_TOKEN`). Do
  not ask the user to paste a personal access token into the conversation, and
  do not echo tokens in commands.
- **Dry run by default.** Preview, then push only on an explicit flag.

## Preferred path: GitHub CLI (`gh`)

`gh` handles auth and is the least error-prone option.

Check it is ready:

```bash
gh --version
gh auth status
```

If `gh auth status` fails, stop and tell the user to run `gh auth login`
themselves (browser or token flow). Do not attempt to authenticate for them.

Create the special repo if it does not exist (public, initialized):

```bash
gh repo view "$USERNAME/$USERNAME" >/dev/null 2>&1 \
  || gh repo create "$USERNAME/$USERNAME" --public --add-readme \
       --description "Profile README"
```

Clone, write, review, push:

```bash
gh repo clone "$USERNAME/$USERNAME" /tmp/profile-repo
cp README.md /tmp/profile-repo/README.md
# copy any assets/ images too
cd /tmp/profile-repo
git add -A
git --no-pager diff --staged        # show the user exactly what changes
# --- get explicit confirmation here ---
git commit -m "Update profile README"
git push
```

## Fallback: REST API via `gh api`

Read the current README (returns base64 `content` and the `sha` you need to
update it):

```bash
gh api "repos/$USERNAME/$USERNAME/contents/README.md"
```

Create or update the README (`sha` is required only when updating an existing
file):

```bash
gh api --method PUT "repos/$USERNAME/$USERNAME/contents/README.md" \
  -f message="Update profile README" \
  -f content="$(base64 -w0 README.md)" \
  -f sha="$EXISTING_SHA"
```

## Fallback: raw REST with a token in the environment

Only if `gh` is unavailable and the user already has a token exported. The token
stays in their environment; never print it.

```bash
curl -sS -X PUT \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$USERNAME/$USERNAME/contents/README.md" \
  -d "$(jq -n --arg m "Update profile README" \
             --arg c "$(base64 -w0 README.md)" \
             --arg s "$EXISTING_SHA" \
             '{message:$m, content:$c, sha:$s}')"
```

## Reading an existing profile without auth

To inspect a live profile before editing (no token needed):

```
https://raw.githubusercontent.com/USERNAME/USERNAME/main/README.md
```

Try `master` if `main` returns 404.

## After deploying

Give the user the two links to check:

- The repo: `https://github.com/USERNAME/USERNAME`
- The rendered profile: `https://github.com/USERNAME`

If images or cards do not appear, the usual causes are a wrong asset path, a
branch mismatch in a raw URL, or a network stripping external SVGs.
