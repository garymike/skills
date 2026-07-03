# Dynamic add-ons (opt-in)

These are optional. Offer them as a menu after the core profile is live; never
add them by default. Present the trade-offs in one line each and let the user
choose.

The tools and their URLs below are the well-known, widely-used options as of this
skill's writing. Third-party services change: verify the current usage on each
project's README before wiring it in, and prefer the project's own latest
instructions if they differ from what is here.

## Quick trade-off summary

- **Rendered-card tools** (stats, streak, trophy, activity graph) are external
  SVG services. They can be slow, occasionally rate-limited, and are stripped by
  some corporate networks. Great on a personal/peer-facing profile; think twice
  for a strictly recruiter-facing one.
- **Actions-based tools** (snake, activity feed, WakaTime) commit generated
  content back into the repo on a schedule. They add a workflow file and
  scheduled runs, but the output is a static committed file, so it always loads.

---

## 1. Stats card

[github-readme-stats](https://github.com/anuraghazra/github-readme-stats).
Live card of commits, stars, PRs, issues.

```markdown
![Stats](https://github-readme-stats.vercel.app/api?username=USERNAME&show_icons=true&hide_border=true&theme=THEME)
```

Top-languages variant:

```markdown
![Top languages](https://github-readme-stats.vercel.app/api/top-langs/?username=USERNAME&layout=compact&hide_border=true&theme=THEME)
```

Tips: set `theme=` to match the accent; `hide_border=true` looks cleaner; the
public instance can be slow, and heavy users sometimes self-host it.

## 2. Streak stats

[github-readme-streak-stats](https://github.com/DenverCoder1/github-readme-streak-stats).

```markdown
![Streak](https://streak-stats.demolab.com?user=USERNAME&hide_border=true&theme=THEME)
```

## 3. Trophies

[github-profile-trophy](https://github.com/ryo-ma/github-profile-trophy).
Can look busy; use a low `column` count and a matching theme, or skip.

```markdown
![Trophies](https://github-profile-trophy.vercel.app/?username=USERNAME&column=4&theme=THEME&no-frame=true)
```

## 4. Activity graph

[github-readme-activity-graph](https://github.com/Ashutosh00710/github-readme-activity-graph).

```markdown
![Activity](https://github-readme-activity-graph.vercel.app/graph?username=USERNAME&hide_border=true&theme=THEME)
```

## 5. Contribution snake (Actions-based)

[Platane/snk](https://github.com/Platane/snk) generates an SVG of a snake eating
the contribution graph, committed to a branch by a scheduled Action. Because the
output is committed, it always renders.

Workflow file at `.github/workflows/snake.yml`:

```yaml
name: generate snake
on:
  schedule:
    - cron: "0 */12 * * *"
  workflow_dispatch:
permissions:
  contents: write
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: Platane/snk@v3
        with:
          github_user_name: ${{ github.repository_owner }}
          outputs: |
            dist/snake.svg
            dist/snake-dark.svg?palette=github-dark
      - uses: crazy-max/ghaction-github-pages@v4
        with:
          target_branch: output
          build_dir: dist
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Embed in the README:

```html
<picture>
  <source media="(prefers-color-scheme: dark)"
    srcset="https://raw.githubusercontent.com/USERNAME/USERNAME/output/snake-dark.svg">
  <img alt="Contribution snake"
    src="https://raw.githubusercontent.com/USERNAME/USERNAME/output/snake.svg">
</picture>
```

Note: this adds a workflow with `contents: write` and a scheduled run. Point that
out so the user is choosing it knowingly.

## 6. Recent activity / blog feed (Actions-based)

- [github-activity-readme](https://github.com/jamesgeorge007/github-activity-readme)
  injects recent GitHub activity between comment markers on a schedule.
- The blog-post-workflow action can pull an RSS feed (e.g. a personal blog) into
  the README the same way.

Both work by finding marker comments in the README and rewriting between them:

```markdown
<!-- START_SECTION:activity -->
<!-- END_SECTION:activity -->
```

## 7. Typing SVG header

[readme-typing-svg](https://github.com/DenverCoder1/readme-typing-svg). An
animated header. One tasteful line beats several.

```markdown
![Typing](https://readme-typing-svg.demolab.com?lines=YOUR+TAGLINE+HERE&font=Fira+Code&center=true&color=ACCENTHEX)
```

## 8. WakaTime coding stats (Actions-based)

[waka-readme-stats](https://github.com/anmol098/waka-readme-stats) writes a
breakdown of coding time into the README between markers on a schedule. Requires
a WakaTime account and a repo secret. Only suggest it if the user already uses
WakaTime.

---

## Placement

Group whatever the user picks under a single "Stats" or "Activity" section rather
than scattering cards through the page. Keep the accent `theme`/`color`
consistent with the rest of the profile.
