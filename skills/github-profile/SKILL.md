---
name: github-profile
description: >-
  Design, build, refresh, and manage a GitHub profile README (the special
  username/username repository, named exactly the same as the account username,
  whose README.md renders at the top of the GitHub profile page). Use this
  whenever the user mentions their GitHub
  profile, profile README, "the README that shows on my GitHub", profile page,
  or wants to add a banner, badges, tech-stack icons, stats cards, a project
  showcase, or a contact section to their profile. Also use to set up the
  special username repo for the first time, redesign an existing profile, or add
  profile automation (auto-updating stats, recent-activity feeds, the
  contribution snake). Trigger even when the user does not say "skill" or
  "README" explicitly but is clearly asking to improve how their GitHub profile
  looks to visitors, recruiters, or collaborators.
license: MIT
---

# GitHub Profile

Build and maintain a standout GitHub profile README: the `README.md` inside a
repository named exactly the same as the account's username. GitHub renders that
file at the top of `github.com/<username>`, so it is the single highest-leverage
piece of a developer's public presence.

This skill covers three jobs that share one pipeline:

- **Design** a profile from scratch (new special repo, first README).
- **Update** an existing profile (edit sections, restyle, add content).
- **Manage** it over time (deploy changes, wire up optional automation).

## The pipeline

Work through these phases in order. Each phase points to a reference file when
you need the full catalog. Keep the reference files closed until you reach the
phase that needs them, so the context stays lean.

1. **Orient** — figure out whether this is a new profile or an edit, and pull in
   what you already know about the person.
2. **Interview the style** — the user chose to be asked each time, so always run
   the short style interview below before writing markdown.
3. **Gather content** — collect the real substance (who they are, what they
   build, links).
4. **Assemble the README** — compose sections from the block library.
5. **Deploy** — write it to the `<username>/<username>` repo, with a hard
   confirmation gate before anything becomes public.
6. **Offer add-ons** — propose optional automation, only if the user wants it.

---

## 1. Orient

Determine the starting point:

- **New profile?** Confirm the exact GitHub username. The special repo must be
  named identically (case-sensitive match to the username). If the repo does not
  exist yet, you will create it in the deploy phase.
- **Existing profile?** Ask for the username (or the repo URL) and read the
  current README first with `gh api` or by fetching
  `https://raw.githubusercontent.com/<username>/<username>/main/README.md`
  (try `master` if `main` 404s). Never rewrite blind. Show the user what is
  there and edit from it.

Pull in context you already have about the person: their field, seniority,
projects, the audience they are writing for (recruiters vs. open-source peers
vs. clients). A profile aimed at hiring managers reads very differently from one
aimed at fellow maintainers. If you do not know the audience, ask.

**Privacy guard — check repo visibility before you list anything.** When you
enumerate repos to draw on (e.g. `gh repo list`), the authenticated owner's view
includes *private* repos. Never surface a private repo's name, description, or
existence in a public README without the user explicitly asking for it. Default
to public repos only. Get the visibility flag up front:

```
gh repo list <username> --json name,description,visibility,isFork
```

and treat anything not `PUBLIC` as off-limits unless the user confirms otherwise.

---

## 2. Interview the style

Always ask, even for edits (the design can shift). Keep it to a handful of
tappable choices, not an essay. Offer these axes:

- **Direction** — pick one:
  - *Minimal & professional*: clean type, a tight header, few or no badges,
    whitespace. Reads as senior and confident.
  - *Rich & dynamic*: banner image, colored badges, tech-stack icon wall, live
    stats cards, trophies. Reads as energetic and thorough.
  - *Terminal / dev-native*: monospace framing, code-block "whoami", ASCII or
    typing-SVG header. Reads as hacker-craftsman.
  - *Editorial / narrative*: prose-forward, a strong opening line, projects told
    as short stories. Reads as thoughtful and human.
- **Accent color** — one or two hex colors to theme badges and cards. Offer to
  match their existing brand if they have one.
- **Density** — how much do they want on the page? A recruiter-facing profile is
  usually better short.

Do not lock these in silently. Reflect the chosen direction back in one line
before you build ("Going terminal-native, cyan accent, medium density.").

For the full design philosophy (avoiding the generic AI-README look, layout
patterns, contrast, restraint), read `references/badges-and-visuals.md`.

---

## 3. Gather content

A profile is only as good as its substance. Collect, in the user's own voice:

- **Identity line** — one sentence on who they are and what they do. This is the
  most-read line on the page; make it specific, not "passionate developer".
- **Focus areas** — what they actually work on now, and what they want more of.
- **Signature achievements** — 2 to 5 concrete wins, ideally quantified (impact,
  scale, adoption), not a duties list. "Cut build times 40%" beats "worked on
  performance". Skip this rather than pad it with vague filler.
- **Featured work** — 2 to 5 repos or projects, each with a one-line "why it
  matters". Real links. **Public repos only by default** (see the privacy guard
  in §1); confirm before featuring anything private, and never leak a private
  repo's name or description.
- **Tech** — the tools worth signaling (only what is true and relevant; a wall
  of every language they touched once is noise).
- **Credentials** — degrees, certifications, or notable awards, if they are
  relevant to the audience. Omit when they add nothing.
- **Collaboration** — what they are open to: contributions, mentoring, speaking,
  consulting, hiring conversations. A specific invitation reads better than a
  generic "open to opportunities".
- **Contact / links** — site, LinkedIn, and any professional handles they want
  public. Ask before publishing any contact detail.
- **Optional flavor** — current learning or a human touch (music, sport, a
  hobby) if it fits the audience.

Write copy that sounds like a person, not a template. Match the user's phrasing
and their existing writing style if you have samples. Avoid filler adjectives.

---

## 4. Assemble the README

Compose the page from modular blocks. The full library (header/banner variants,
about, skills grids, project cards, stats, contact, footer) with copy-paste
markdown and HTML lives in `references/content-blocks.md`. Read it now.

Starter scaffolds for each style direction are in `assets/templates/`
(`minimal.md`, `rich.md`, `terminal.md`, `editorial.md`). Load the one that
matches the chosen direction, then swap in the real content. Templates are
starting points, not straitjackets; cut anything that does not earn its place.

Assembly rules that keep profiles from looking generic:

- **Lead with the identity line**, not a giant "Hi 👋 I'm..." banner unless the
  banner is genuinely good.
- **Every badge must mean something.** Skip badges for skills they would not
  want to be interviewed on.
- **Prefer quantified impact over adjectives.** "Cut build times 40%" beats
  "passionate about performance". Numbers and outcomes read as senior; filler
  adjectives read as generic.
- **Prefer real links over decoration.** A visitor should reach the work in one
  click.
- **Alt text on every image**, and keep the page readable with images blocked
  (many corporate networks strip external images and stats cards).
- **Test the raw-markdown fallback**: if all the fancy SVGs fail to load, the
  page should still read as a competent profile.

Write the final file to the working directory (e.g.
`/home/claude/profile-build/README.md`) so the user can review it before
anything is deployed.

---

## 5. Deploy

The user opted for API-driven deployment. Drive it with the GitHub CLI (`gh`),
which handles auth cleanly, and fall back to the REST API only if needed. Full
commands, auth handling, and the token fallback are in
`references/github-api.md`. The helper script `scripts/deploy_profile.py`
wraps the safe path.

**Hard rules for this phase:**

- **Confirm before publishing.** Creating the repo, committing, and pushing all
  make content public on the user's account. Show the user the final README and
  get an explicit "yes, publish it" before any push. Never generalize one
  approval to later edits; ask each time you push.
- **Never handle tokens in chat.** Authenticate via `gh auth login` (or a token
  already in the user's environment). Do not ask the user to paste a personal
  access token into the conversation, and do not put tokens in commands you echo
  back.
- **Default to a dry run.** The deploy script previews what it will do without
  pushing unless it is invoked with an explicit publish flag.
- **Preserve what exists.** For an edit, diff against the live README so the user
  sees exactly what changes.

Typical flow:

1. Verify `gh` is installed and authenticated (`gh auth status`). If not, tell
   the user how to authenticate; do not attempt to log in for them.
2. Ensure the `<username>/<username>` repo exists (create it public with a README
   if missing).
3. Write the composed `README.md` (and any `assets/` images) into a local clone.
4. Show the diff. Get explicit confirmation.
5. Commit and push.

---

## 6. Offer add-ons (opt-in)

Only after the core profile is live, offer dynamic automation as options; do not
add them by default. The catalog (stats cards, streak stats, trophies, activity
feed, contribution snake, WakaTime, typing SVG), with exact snippets and the
GitHub Actions workflows some of them need, is in `references/dynamic-addons.md`.

Present them as a short menu and let the user pick. Flag the trade-offs briefly:
external stats cards can be slow or rate-limited and may not render on some
networks; GitHub Actions add a workflow file and scheduled runs to the repo.

---

## Reference files

- `references/content-blocks.md` — the section library: every README block as
  copy-paste markdown/HTML, with variants.
- `references/badges-and-visuals.md` — badge systems (shields.io, simple-icons),
  color and layout guidance, and how to avoid the generic AI-README look.
- `references/dynamic-addons.md` — opt-in automation: stats cards, snake,
  activity feeds, and the Actions workflows they need.
- `references/github-api.md` — deploying via `gh` and the REST API, auth, the
  token fallback, and the confirmation gate.

## Assets

- `assets/templates/minimal.md`
- `assets/templates/rich.md`
- `assets/templates/terminal.md`
- `assets/templates/editorial.md`

## Scripts

- `scripts/deploy_profile.py` — safe deploy wrapper (dry-run by default, creates
  the special repo if missing, pushes only with an explicit flag).
