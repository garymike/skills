#!/usr/bin/env python3
"""Deploy a GitHub profile README to the special <username>/<username> repo.

Safe by design:
  * Dry-run by default. It previews the diff and does NOT push unless you pass
    --publish.
  * Uses the GitHub CLI (`gh`) for auth and git operations. It never reads,
    prints, or asks for a token.
  * Creates the special repo (public) only if it does not already exist.

Usage:
    # preview what would change (no push):
    python deploy_profile.py --username USER --readme path/to/README.md

    # actually publish (after the user has confirmed):
    python deploy_profile.py --username USER --readme path/to/README.md \
        --assets path/to/assets --publish

Exit codes: 0 ok, 1 precondition failed, 2 git/gh error.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd, **kw):
    """Run a command, returning CompletedProcess. Never logs env/secrets."""
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def require_gh():
    if shutil.which("gh") is None:
        sys.exit(
            "error: the GitHub CLI `gh` is not installed.\n"
            "Install it (https://cli.github.com) or use the REST fallback in "
            "references/github-api.md."
        )
    auth = run(["gh", "auth", "status"])
    if auth.returncode != 0:
        sys.exit(
            "error: `gh` is not authenticated.\n"
            "Ask the user to run `gh auth login` themselves. Do not attempt to "
            "authenticate on their behalf or handle their token."
        )


def repo_exists(slug):
    return run(["gh", "repo", "view", slug]).returncode == 0


def main():
    ap = argparse.ArgumentParser(description="Deploy a GitHub profile README.")
    ap.add_argument("--username", required=True, help="GitHub username (repo is USER/USER).")
    ap.add_argument("--readme", required=True, type=Path, help="Path to the composed README.md.")
    ap.add_argument("--assets", type=Path, default=None, help="Optional directory of images to copy into assets/.")
    ap.add_argument("--message", default="Update profile README", help="Commit message.")
    ap.add_argument("--publish", action="store_true", help="Actually commit and push. Omit for a dry run.")
    args = ap.parse_args()

    if not args.readme.is_file():
        sys.exit(f"error: readme not found: {args.readme}")

    require_gh()

    slug = f"{args.username}/{args.username}"

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "repo"

        if repo_exists(slug):
            clone = run(["gh", "repo", "clone", slug, str(work)])
            if clone.returncode != 0:
                sys.exit(f"error: could not clone {slug}:\n{clone.stderr}")
        else:
            print(f"note: {slug} does not exist yet.")
            if not args.publish:
                print("dry run: would create it as a public repo on --publish.")
                work.mkdir(parents=True)
            else:
                created = run([
                    "gh", "repo", "create", slug, "--public",
                    "--add-readme", "--description", "Profile README",
                ])
                if created.returncode != 0:
                    sys.exit(f"error: could not create {slug}:\n{created.stderr}")
                run(["gh", "repo", "clone", slug, str(work)])

        # Stage the new content.
        shutil.copyfile(args.readme, work / "README.md")
        if args.assets and args.assets.is_dir():
            dest = work / "assets"
            dest.mkdir(exist_ok=True)
            for f in args.assets.iterdir():
                if f.is_file():
                    shutil.copyfile(f, dest / f.name)

        is_git = (work / ".git").is_dir()
        if is_git:
            run(["git", "-C", str(work), "add", "-A"])
            diff = run(["git", "-C", str(work), "--no-pager", "diff", "--staged"])
            print("\n===== staged changes =====")
            print(diff.stdout or "(no textual diff; likely new/binary files)")
            print("==========================\n")

        if not args.publish:
            print("DRY RUN. Nothing was pushed.")
            print("Re-run with --publish once the user has explicitly approved.")
            return

        if not is_git:
            sys.exit("error: no git repo to push into. Re-run without --publish first to inspect.")

        commit = run(["git", "-C", str(work), "commit", "-m", args.message])
        if commit.returncode != 0 and "nothing to commit" in (commit.stdout + commit.stderr):
            print("nothing to commit; the README already matches. Done.")
            return
        if commit.returncode != 0:
            sys.exit(f"error: commit failed:\n{commit.stderr or commit.stdout}")

        push = run(["git", "-C", str(work), "push"])
        if push.returncode != 0:
            sys.exit(f"error: push failed:\n{push.stderr}")

        print(f"Published. View: https://github.com/{args.username}")


if __name__ == "__main__":
    main()
