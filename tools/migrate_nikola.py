#!/usr/bin/env python3
"""Migrate the old Nikola blog posts to Quarto.

Reads the legacy sources from the last Nikola commit (git show 7f547e5:…), so the
old files don't need to stay in the working tree, and the script can be re-run
any time.

    python3 tools/migrate_nikola.py            # (re)generate posts + manifest
    python3 tools/migrate_nikola.py --propose  # ignore manifest decisions, re-propose

Workflow
--------
1. Run it once. It writes tools/posts_manifest.csv with a proposed
   keep/hide decision for every post (column `decision`).
2. Edit the `decision` column (keep | hide).
3. Run it again. Hidden posts get `draft: true` and are left out of the build.

Output: site/blog/archive/YYYY-MM-DD-slug/index.qmd (directory is wiped and
rebuilt on each run, so don't hand-edit files there until you're done
curating; after that, just edit the posts directly and stop running this).
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "blog" / "archive"
MANIFEST = ROOT / "tools" / "posts_manifest.csv"
SOURCE_REF = "7f547e5"  # last Nikola commit (old posts live here)
QUARTO = shutil.which("quarto") or "/usr/local/bin/quarto"

SOURCES = {
    "huwp": "Harvard WordPress blog (2005–2008)",
    "drupal": "Courant Drupal site (2008–2011)",
    "nikola": "Nikola blog (2016–2018)",
}
BANNER = {
    "huwp": (
        "This post is from the blog I kept as Preceptor in Mathematics at "
        "Harvard (2005–2008). It's kept here as an archive; some links are dead "
        "and references are dated."
    ),
    "drupal": (
        "This post is from the site I kept at the Courant Institute "
        "(2008–2011). It's kept here as an archive; some links are dead and "
        "references are dated."
    ),
}

# ---------------------------------------------------------------- curation
HIDE_CATEGORIES = ("leisure", "family", "new york", "miscellaneous")
HIDE_PATTERNS = [
    # personal / leisure
    (r"citi-?bike|running-journal|brisket|philadelphia|move-on-up|geek-lust|nawlins|"
     r"anarchists|new-toys|hooray-for-boston", "personal"),
    # sports and pop-culture link posts
    (r"nfl|cowboys|ravens|baseball|jason-lezak|james-bond|numb3rs|weapons-of-math|"
     r"donald-in-mathmagic|tell-me-tell-me|separated|spirit-airlines|lottery|"
     r"psychologist|math-is-hot|math-will-rock|if-the-irs|funny|fun-and-games|"
     r"what-you-know|kids-are-all-right|lauderdale|aol-fails|sputnik|food-math|"
     r"thatfeelingwhen|tfw-", "pop culture / humor link post"),
    # blog housekeeping and gadget notes
    (r"hello-world|drupal-progress|dumping-a-wordpress|back-again|blogged-likes|"
     r"wordpress-upgraded|^flock|eff-pee|macbook-pro|itunes|microsoft-spurns|"
     r"are-we-still-here|yikes|reading-list|wednesday-links|^1$|^4$|^5$|^7$|"
     r"christmas-presents|disk-utility|php-5|review-of-no-nonsense|"
     r"movin-down|move-complete|move-is-complete", "blog housekeeping / dated tech"),
    # ephemeral course logistics
    (r"roundup|sectioning|syllabus-is-online|tums-ii-syllabus|placement-exam|"
     r"math-20-or-21|ap-calculus|spring-1a|happy-spring-term|happy-first-day|"
     r"happy-holidays|upcoming|summer-school", "dated course logistics"),
]


def propose(slug: str, category: str) -> tuple[str, str]:
    cat = (category or "").lower()
    if cat.startswith(HIDE_CATEGORIES):
        return "hide", f"category '{category}'"
    for pat, why in HIDE_PATTERNS:
        if re.search(pat, slug):
            return "hide", why
    return "keep", ""


# ---------------------------------------------------------------- reading
def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def list_sources() -> list[tuple[str, str]]:
    out = []
    for path in git("ls-tree", "-r", "--name-only", SOURCE_REF, "posts/").splitlines():
        if path.startswith("posts/huwp/") and path.endswith(".html"):
            out.append(("huwp", path))
        elif path.startswith("posts/drupal/") and path.endswith(".html"):
            out.append(("drupal", path))
        elif re.fullmatch(r"posts/[^/]+\.(rst|txt)", path):
            out.append(("nikola", path))
    return out


META_RE = re.compile(r"^\.\.\s+([a-z_]+):\s?(.*)$")


def split_meta(text: str, is_html: bool) -> tuple[dict, str]:
    meta: dict[str, str] = {}
    if is_html:
        m = re.match(r"\s*<!--(.*?)-->", text, re.S)
        head, body = (m.group(1), text[m.end():]) if m else ("", text)
        lines = head.splitlines()
    else:
        lines, rest = [], text.splitlines(keepends=True)
        while rest and (META_RE.match(rest[0].rstrip("\n")) or not rest[0].strip()) and len(lines) < 30:
            line = rest.pop(0)
            if line.strip():
                lines.append(line.rstrip("\n"))
            elif lines:
                break
        body = "".join(rest)
    for line in lines:
        m = META_RE.match(line.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta, body


def parse_date(s: str) -> str:
    m = re.match(r"(\d{4}-\d{2}-\d{2})", s or "")
    if not m:
        raise ValueError(f"bad date {s!r}")
    return m.group(1)


def split_tags(s: str) -> list[str]:
    tags = [t.strip() for t in re.split(r",", s or "") if t.strip()]
    seen, out = set(), []
    for t in tags:
        if t.lower() not in seen and t.lower() != "mathjax":
            seen.add(t.lower())
            out.append(t)
    return out


# ---------------------------------------------------------------- converting
def pandoc(text: str, fmt: str) -> str:
    r = subprocess.run([QUARTO, "pandoc", "-f", fmt, "-t", "markdown-smart",
                        "--wrap=none", "--lua-filter",
                        str(ROOT / "tools" / "strip_legacy_ids.lua")], input=text, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return r.stdout


def clean_html(body: str) -> str:
    body = re.sub(r"</?(html|body)>", "", body)
    body = re.sub(r'<div class="alert[^"]*"[^>]*>.*?</div>', "", body, count=1, flags=re.S)
    return body


def media(url: str) -> str:
    if re.search(r"youtube\.com|youtu\.be|vimeo\.com", url):
        return "{{< video " + url + " >}}"
    if "instagram.com" in url:
        return f"[View this photo on Instagram]({url})"
    if "twitter.com" in url:
        return f"[View this post on Twitter]({url})"
    return f"<{url}>"


def postprocess(md: str, slug_map: dict[str, str]) -> str:
    # Don't let stray shortcode syntax in old text be interpreted by Quarto
    # (must happen before we insert our own {{< video >}} shortcodes).
    md = md.replace("{{<", "{{</*").replace(">}}", "*/>}}")
    # Nikola directives that pandoc turns into divs
    md = re.sub(r"::: media\n<?([^\s>]+)>?\n:::", lambda m: media(m.group(1)), md)
    md = re.sub(r"::: youtube\n(\S+)\n:::",
                lambda m: "{{< video https://www.youtube.com/watch?v=" + m.group(1) + " >}}", md)
    md = re.sub(r"::: gist\n(\S+)\n:::",
                lambda m: f'```{{=html}}\n<script src="https://gist.github.com/leingang/{m.group(1)}.js"></script>\n```', md)
    # Nikola cross-links
    def link(m):
        target = slug_map.get(m.group(1))
        return target if target else f"/posts/{m.group(1)}/"
    md = re.sub(r"link://slug/([\w-]+)", link, md)
    return md.strip() + "\n"


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--propose", action="store_true",
                    help="ignore existing manifest decisions")
    args = ap.parse_args()

    decisions: dict[str, tuple[str, str]] = {}
    if MANIFEST.exists() and not args.propose:
        with MANIFEST.open() as f:
            for row in csv.DictReader(f):
                decisions[row["slug"]] = (row["decision"].strip().lower(), row["reason"])

    posts = []
    for source, path in list_sources():
        text = git("show", f"{SOURCE_REF}:{path}")
        meta, body = split_meta(text, path.endswith(".html"))
        slug = meta.get("slug") or Path(path).stem
        date = parse_date(meta.get("date", ""))
        posts.append(dict(source=source, path=path, meta=meta, body=body,
                          slug=slug, date=date, dir=f"{date}-{slug}"))

    slugs = [p["slug"] for p in posts]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        print("WARNING duplicate slugs:", dupes, file=sys.stderr)
    slug_map = {p["slug"]: f"/blog/archive/{p['dir']}/" for p in posts}

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    rows = []
    for p in sorted(posts, key=lambda p: p["date"]):
        meta, source, slug = p["meta"], p["source"], p["slug"]
        category = meta.get("category", "")
        if slug in decisions:
            decision, reason = decisions[slug]
        else:
            decision, reason = propose(slug, category)

        if source == "nikola":
            md = pandoc(p["body"], "rst")
        else:
            md = pandoc(clean_html(p["body"]), "html+tex_math_single_backslash+raw_html")
        md = postprocess(md, slug_map)

        cats = []
        if category:
            cats.append(category.split("/")[-1].replace("-", " "))
        for t in split_tags(meta.get("tags", "")):
            if t.lower() not in {c.lower() for c in cats}:
                cats.append(t)
        front = {
            "title": meta.get("title") or slug,
            "date": p["date"],
            "categories": cats,
            "legacy-source": source,
        }
        if meta.get("description"):
            front["description"] = meta["description"]
        if decision == "hide":
            front["draft"] = True
        else:
            front["aliases"] = [f"/posts/{slug}/", f"/posts/{slug}/index.html"]

        banner = ""
        if source in BANNER:
            banner = ('::: {.callout-note .legacy appearance="simple"}\n'
                      f"{BANNER[source]}\n:::\n\n")
        d = OUT / p["dir"]
        d.mkdir()
        (d / "index.qmd").write_text(
            "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=1000)
            + "---\n\n" + banner + md, encoding="utf-8")

        rows.append(dict(decision=decision, date=p["date"], source=source, slug=slug,
                         title=front["title"], category=category,
                         tags=", ".join(split_tags(meta.get("tags", ""))), reason=reason))

    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    kept = sum(r["decision"] == "keep" for r in rows)
    print(f"{len(rows)} posts written to {OUT.relative_to(ROOT)}: "
          f"{kept} keep, {len(rows) - kept} hide. Manifest: {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
