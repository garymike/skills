#!/usr/bin/env bash
#
# Keep the manifest version, CHANGELOG.md, the git tags and the GitHub Releases
# telling the same story.
#
# CLAUDE.md already says to bump both manifests, record the change in
# CHANGELOG.md, tag the release commit and cut a Release. Nothing enforced it,
# so it drifted: 0.8.0 and 0.8.1 were bumped, changelogged and merged, and then
# never tagged or released. Tags stopped at v0.7.1 while the manifest said
# 0.8.1, and nobody noticed for two releases because every signal a human looks
# at was green. This is the same shape as the workflow-health and
# updater-health checks in the github-security-audit skill: verify the thing
# actually happened rather than trusting it was configured to.
#
# Two modes, because the convention is bump-in-PR then tag-after-merge, so a
# single gate cannot be right for both:
#
#   --pr         What is checkable while the PR is open. The tag cannot exist
#                yet, so it is not required. Never red by design.
#   --released   Whether the version on main actually got a tag and a Release.
#                Run on a schedule, not on push: it is legitimately red for the
#                gap between merging and tagging, and a gate that goes red after
#                every merge regardless of how promptly anyone acts is the
#                cry-wolf signal .github/dependabot.yml warns about.
#
# Usage: check-release-consistency.sh --pr | --released
# Exit:  0 = consistent, 1 = a mismatch worth acting on, 2 = bad invocation.
#
# --released needs `gh` authenticated with contents:read to list Releases.

set -uo pipefail

MODE="${1:-}"
case "$MODE" in
  --pr|--released) ;;
  *) echo "usage: $(basename "$0") --pr | --released" >&2; exit 2 ;;
esac

cd "$(dirname "$0")/.."

PLUGIN=.claude-plugin/plugin.json
MARKET=.claude-plugin/marketplace.json
fail=0

note()  { echo "  $*"; }
bad()   { echo "::error::$*"; fail=1; }
warn()  { echo "::warning::$*"; }

# --- the manifests must agree with each other ---------------------------------
# marketplace.json carries the version twice (top level and under plugins[]).
# A sed-based bump that catches one and misses the other is the easy mistake,
# so every occurrence is compared, not just the first.
#
# Extracted with grep rather than jq so this runs anywhere, including a Git Bash
# checkout with no jq installed. These manifests are small and flat, and the
# pattern is anchored to a single line. An earlier jq version of this failed on
# a machine without jq by reporting "has no version field" — a check that fails
# for the wrong reason and states something false is worse than no check.
extract_versions() {
  grep -oE '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$1" | sed 's/.*"\([^"]*\)"$/\1/'
}

VER=$(extract_versions "$PLUGIN" | head -1)
mapfile -t MARKET_VERS < <(extract_versions "$MARKET")

note "manifest version: ${VER:-<none found>}"
note "marketplace versions: ${MARKET_VERS[*]:-<none found>}"

if [ -z "$VER" ]; then
  bad "could not read a \"version\" field from $PLUGIN — is the file present and valid JSON?"
  exit 1
fi

if [ "${#MARKET_VERS[@]}" -eq 0 ]; then
  bad "could not read any \"version\" field from $MARKET"
fi

if ! printf '%s' "$VER" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  bad "version '$VER' in $PLUGIN is not plain semver (MAJOR.MINOR.PATCH)"
fi

for mv in "${MARKET_VERS[@]:-}"; do
  if [ "$mv" != "$VER" ]; then
    bad "$MARKET has version '$mv' but $PLUGIN says '$VER' — every occurrence must match"
  fi
done

# --- the changelog must describe this version ---------------------------------
if ! grep -qE "^## \[${VER//./\\.}\] - " CHANGELOG.md; then
  bad "CHANGELOG.md has no '## [$VER] - <date>' entry. CLAUDE.md requires the entry in the same commit as the bump"
fi

# --- the version must not move backwards -------------------------------------
# Tags are the released history. Fetch them so a shallow CI checkout can see
# them; without this the newest tag reads as empty and the comparison is a no-op
# that silently passes.
git fetch --tags --quiet --force 2>/dev/null || warn "could not fetch tags; comparison against released history may be incomplete"
NEWEST_TAG=$(git tag -l 'v[0-9]*' | sed 's/^v//' | sort -V | tail -1)

if [ -n "$NEWEST_TAG" ]; then
  note "newest released tag: v$NEWEST_TAG"
  LOWEST=$(printf '%s\n%s\n' "$VER" "$NEWEST_TAG" | sort -V | head -1)
  if [ "$VER" != "$NEWEST_TAG" ] && [ "$VER" = "$LOWEST" ]; then
    bad "manifest version $VER is older than the newest tag v$NEWEST_TAG — a bump must move forward"
  fi
else
  warn "no v* tags found; skipping the backwards-version check"
fi

# --- PR mode stops here ------------------------------------------------------
if [ "$MODE" = "--pr" ]; then
  [ "$fail" -eq 0 ] && echo "Manifests, CHANGELOG.md and version ordering are consistent."
  exit "$fail"
fi

# --- released mode: did the tag and the Release actually happen? --------------
TAG="v$VER"

if ! git rev-parse -q --verify "refs/tags/$TAG" >/dev/null; then
  bad "manifest is at $VER but there is no $TAG tag. Tag the commit that bumped it: git tag -a $TAG -m '...' && git push origin $TAG"
else
  note "tag $TAG exists"

  # Annotated, per CLAUDE.md. A lightweight tag points straight at a commit;
  # an annotated one is its own object, so the type tells them apart.
  if [ "$(git cat-file -t "$TAG" 2>/dev/null)" != "tag" ]; then
    bad "$TAG is a lightweight tag; CLAUDE.md asks for annotated (git tag -a)"
  fi

  # The tag must be on the default branch, not stranded on a feature branch.
  if ! git merge-base --is-ancestor "$TAG^{commit}" origin/main 2>/dev/null; then
    bad "$TAG is not reachable from origin/main — tag the release commit on main, not a branch"
  fi
fi

# gh has its own built-in jq via -q, so this needs no external jq either.
if command -v gh >/dev/null 2>&1; then
  DRAFT=$(gh release view "$TAG" --json isDraft -q '.isDraft' 2>/dev/null)
  if [ -z "$DRAFT" ]; then
    bad "no GitHub Release for $TAG. Cut one reusing that version's CHANGELOG.md entry: gh release create $TAG --notes-file <notes>"
  elif [ "$DRAFT" = "true" ]; then
    bad "the Release for $TAG is still a draft"
  else
    note "release $TAG is published"
  fi
else
  warn "gh not available; skipped the Release check"
fi

if [ "$fail" -eq 0 ]; then
  echo "Version $VER is changelogged, tagged as $TAG, and released."
fi
exit "$fail"
