# Matthew Leingang: office page and professional site

One repository, two [Quarto](https://quarto.org) sites that share data:

| Directory | Publishes to | Look |
|---|---|---|
| `office/` | <https://cims.nyu.edu/~mpl5/> | Near-replica of math.nyu.edu (department header, nav, footer) |
| `site/` | <https://www.matthewleingang.com/> | Professional site; same typography, its own palette, no NYU branding |
| `_shared/` | (both) | `person.yml` (contact/profile), `teaching.yml` (courses, office hours), `headshot.jpg` |

Requires Quarto ≥ 1.5 (`quarto --version`). Python 3 + PyYAML only for the migration tool.

## Common tasks

### New term: update courses and office hours
1. Edit `_shared/teaching.yml`: `term`, `office-hours`, `current-courses`; move last term's courses into `past-courses`.
2. `make preview-office` to check, then `make deploy-office-dry` and `make deploy-office`.
3. Push to GitHub so the "Courses taught" table on matthewleingang.com updates too.

### Change contact info, title, publications
Edit `_shared/person.yml`. Both sites pick it up.

### Write a blog post
```sh
mkdir site/blog/posts/2026-12-01-my-post
$EDITOR site/blog/posts/2026-12-01-my-post/index.qmd
```
```yaml
---
title: "My post"
date: 2026-12-01
description: "One-sentence summary (shows in listings, RSS, and link previews)."
categories: [teaching, calculus]
---
```
Math works as usual: `$x^2$`, `$$\int f$$`. `make preview-site` to see it; push to publish.
Add `draft: true` to keep a post out of the build.

### Add a talk or project
Append an entry to `site/talks.yml` or `site/projects.yml`.

### CV
`site/cv.qmd` renders to both HTML and `leingang-cv.pdf` (Typst). Edit once; both update.
It was converted from `tex/Leingang_CV.tex` in the `leingang/cv` repo (March 2024) and is now
the maintained copy. The public version leaves out home address and phone.

## Publishing

**Office page → CIMS.** `make deploy-office` runs `rsync --delete` of `office/_site/` to
`mpl5@access.cims.nyu.edu:public_html/`. Override with
`make deploy-office CIMS_USER=… CIMS_DIR=…`. Always run `make deploy-office-dry` first;
`--delete` removes anything else in `public_html/` *except* paths listed in `RSYNC_PROTECT`
in the Makefile (currently `grading/`). Add any other directories you keep there.
The department profile links to `cims.nyu.edu/~leingang`, which may be an alias for `~mpl5`.
After the first deploy, check that both URLs show the page.

**Professional site → GitHub Pages.** `.github/workflows/site.yml` renders `site/` on every
push to `main` that touches `site/` or `_shared/`. One-time setup:
1. Repo Settings → Pages → Source: **GitHub Actions**.
2. Custom domain `www.matthewleingang.com` (from `site/CNAME`). At the DNS registrar: `CNAME www → leingang.github.io`,
   and apex `A` records → 185.199.108.153, .109.153, .110.153, .111.153.
3. Tick "Enforce HTTPS" once the certificate is issued.

## Legacy blog (2005–2018)

The old Nikola site (archived at tag `nikola-final`) had 197 posts from three earlier blogs.
`tools/migrate_nikola.py` converted them with pandoc into `site/blog/archive/`, adding
`aliases` so old URLs (`/posts/<slug>/`) redirect.

Curation is in `tools/posts_manifest.csv` (`decision` = `keep` | `hide`). Edit the CSV, run
`make migrate`, and hidden posts get `draft: true` (excluded from the build). After curation is
final, stop re-running the script (it regenerates `site/blog/archive/` from scratch) and edit
posts directly.

## Office page internals

`office/_partials/template.html` is a Pandoc template that reproduces the markup of a
math.nyu.edu page; `dept-header.html` / `dept-footer.html` were copied from the department
homepage, and `office/assets/math/` holds local copies of the department stylesheet and logos.
If the department redesigns its site, re-copy those from <https://math.nyu.edu/dynamic/>.
