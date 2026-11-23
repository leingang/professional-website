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
Add `draft: true` to keep a post off the live site. Drafts still show (marked as drafts)
when previewing, including the editor's Preview button. Publishing builds use
`--profile production` (`site/_quarto-production.yml`), which leaves them out.

### Import Stack Exchange answers
`tools/import_stackexchange.py` turns my Stack Exchange answers (Math.SE, TeX.SE, Stack Overflow, …) into draft posts in
`drafts/answers/`. Published ones move to `site/blog/answers/` and are listed in their own
section on the Writing page.

Drafts are kept outside the `site/` project on purpose: Quarto reads every `.qmd` in a project
before it builds anything, even drafts, and with ~1,400 drafts inside `site/` every build took
more than ten minutes. `drafts/_quarto.yml` uses the site's theme so previews look right.

1. One time: create `tools/stackexchange.yml` with the numeric user ids from the profile URLs
   (`math.stackexchange.com/users/<id>/…`, `stackoverflow.com/users/<id>/…`):
   ```yaml
   math: 12345
   tex: 678
   stackoverflow: 9
   ```
   Any Stack Exchange site works. The key is the site's API name: usually the subdomain
   (`academia`, `physics`), or the domain for sites outside stackexchange.com
   (`stackoverflow`, `mathoverflow.net`, `superuser`).
2. `make import-se`. Every answer becomes a draft in `drafts/answers/`, and
   `tools/se_manifest.csv` lists them by score. Options: `--min-score N`, `--only ID,ID`,
   `--refresh` (re-download; API responses are cached in `tools/se_cache/`), and
   `--force ID` (regenerate one post; this overwrites your edits).
3. Curate: edit a draft (trim or paraphrase the quoted question, expand the answer) and
   check it with `make preview-post POST=drafts/answers/<folder>` (live reload, a few seconds).
4. `make publish POST=drafts/answers/<folder>` moves it into `site/blog/answers/` and removes
   its `draft: true` line. Then `make preview-site` or push.

Re-running the import never touches existing posts (drafts or published), except to point
links between my answers at the local copy once the target is published.
`make preview-post` also works on any published post, e.g. `POST=site/blog/posts/<folder>`.

Licensing: my answers are mine to republish. The quoted question and others' edits are CC BY-SA,
so each post keeps the generated credit lines (asker, editors, link to the original) and its
`license:` field. Keep those when you edit. If you paraphrase the question instead of quoting it,
the credit for the asker can go, but keep the link.

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
