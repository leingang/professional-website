#!/usr/bin/env python3
"""Import my Stack Exchange answers (Math.SE, TeX.SE, Stack Overflow) as draft blog posts.

    python3 tools/import_stackexchange.py                    # users from tools/stackexchange.yml
    python3 tools/import_stackexchange.py --user math=12345 --user tex=678 --user stackoverflow=9
    python3 tools/import_stackexchange.py --refresh          # re-download from the API
    python3 tools/import_stackexchange.py --min-score 3      # skip low-scoring answers
    python3 tools/import_stackexchange.py --only 21209,250   # just these answer ids
    python3 tools/import_stackexchange.py --force 21209      # regenerate one post (overwrites!)
    python3 tools/import_stackexchange.py --publish drafts/answers/<folder>   # = make publish

Workflow
--------
1. Run it. Every answer becomes drafts/answers/YYYY-MM-DD-<site>-<slug>/index.qmd
   with `draft: true`, and tools/se_manifest.csv lists them all (sort by score).
   Drafts live outside the site/ project on purpose: Quarto reads every .qmd in a
   project before building, so 1,400 drafts there made every build take minutes.
2. Curate by hand: edit the post (trim or paraphrase the quoted question, expand the
   answer). Preview it with `make preview-post POST=drafts/answers/<folder>`.
3. Publish it with `make publish POST=drafts/answers/<folder>`: this moves the folder
   to site/blog/answers/ and deletes the `draft: true` line.
4. Re-running is safe. Existing posts (drafts or published) are never overwritten
   (except with --force). Each run also rewrites links between answers: a link to
   another of my answers points to the local post once that post is published.

Licensing
---------
My answers are mine to republish. The quoted question (and any substantial edits
others made to my answer) are CC BY-SA, so each post credits the asker and editors,
links to the original, and carries the CC BY-SA license of the original post.

API responses are cached in tools/se_cache/ (git-ignored), so re-runs work offline
and don't use up the 300-requests/day anonymous quota.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import html
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "drafts" / "answers"        # new posts go here (outside the site project)
PUBLISHED = ROOT / "site" / "blog" / "answers"
CACHE = ROOT / "tools" / "se_cache"
CONFIG = ROOT / "tools" / "stackexchange.yml"
MANIFEST = ROOT / "tools" / "se_manifest.csv"

API = "https://api.stackexchange.com/2.3"
# Custom filter: default fields + body_markdown, link, title, content_license, revision.user,
# .backoff/.quota_remaining/.has_more. Created once with /filters/create.
FILTER = "!FuhdYD2u)f5mDpBvoZHoGX.h2Y"
USER_AGENT = "quarto-blog-importer/1.0 (personal site)"

# Sites with hand-tuned settings. Any other Stack Exchange site (academia, physics, …)
# is filled in from the API's site list by load_site().
SITES = {
    "math": dict(name="Mathematics Stack Exchange", short="Math.SE", category="math.se",
                 host="math.stackexchange.com", mathjax=True, code_lang=""),
    "tex": dict(name="TeX Stack Exchange", short="TeX.SE", category="tex.se",
                host="tex.stackexchange.com", mathjax=False, code_lang="latex"),
    # code_lang "" here: unlabeled code gets a language from the question's tags (TAG_LANG)
    "stackoverflow": dict(name="Stack Overflow", short="Stack Overflow", category="stackoverflow",
                          host="stackoverflow.com", mathjax=False, code_lang=""),
    "stats": dict(name="Cross Validated", short="Cross Validated", category="stats.se",
                  host="stats.stackexchange.com", mathjax=True, code_lang=""),
}
SITE_ALIASES = {"math.stackexchange": "math", "math.stackexchange.com": "math",
                "tex.stackexchange": "tex", "tex.stackexchange.com": "tex",
                "stackoverflow.com": "stackoverflow", "so": "stackoverflow"}
# Question tag → Pandoc highlighting language, for unlabeled code blocks
# (mirrors how Stack Overflow picks highlighting from tags). First matching tag wins.
TAG_LANG = {
    "python": "python", "python-3.x": "python", "pandas": "python", "numpy": "python",
    "matplotlib": "python", "django": "python", "r": "r", "ggplot2": "r",
    "javascript": "javascript", "node.js": "javascript", "jquery": "javascript",
    "typescript": "typescript", "java": "java", "c": "c", "c++": "cpp", "c#": "cs",
    "php": "php", "ruby": "ruby", "go": "go", "rust": "rust", "swift": "swift",
    "bash": "bash", "shell": "bash", "git": "bash", "zsh": "zsh", "sql": "sql", "mysql": "sql",
    "html": "html", "css": "css", "json": "json", "yaml": "yaml", "xml": "xml",
    "latex": "latex", "tex": "latex", "matlab": "matlab", "julia": "julia",
    "haskell": "haskell", "perl": "perl", "lua": "lua", "elisp": "commonlisp",
    "emacs": "commonlisp", "makefile": "makefile", "dockerfile": "dockerfile",
}


def code_lang_for(site: str, tags: list[str]) -> str:
    if SITES[site]["code_lang"]:
        return SITES[site]["code_lang"]
    if not SITES[site]["mathjax"]:   # Stack Overflow and other code-heavy sites
        for t in tags:
            if t in TAG_LANG:
                return TAG_LANG[t]
    return ""
IMAGE_HOSTS = ("i.sstatic.net", "i.stack.imgur.com", "i.imgur.com")
LONG_QUESTION = 1500   # characters; longer questions get a collapsed callout


# ---------------------------------------------------------------- API
def api_get(path: str, **params) -> dict:
    params = {"filter": FILTER, **params}
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        raw = e.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    data = json.loads(raw)
    if "error_id" in data:
        raise RuntimeError(f"API error {data['error_id']} {data.get('error_name')}: "
                           f"{data.get('error_message')} ({path})")
    if data.get("backoff"):
        print(f"  API asked to back off {data['backoff']}s", file=sys.stderr)
        time.sleep(data["backoff"] + 1)
    if data.get("quota_remaining", 1) < 10:
        print(f"  WARNING: API quota nearly used up ({data['quota_remaining']} left today)",
              file=sys.stderr)
    return data


def api_all(path: str, **params) -> list[dict]:
    items, page = [], 1
    while True:
        data = api_get(path, page=page, pagesize=100, **params)
        items += data["items"]
        if not data.get("has_more"):
            return items
        page += 1
        time.sleep(0.2)


def chunks(xs: list, n: int):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def fetch_site(site: str, user_id: int, refresh: bool) -> tuple[list, dict, dict]:
    """Return (answers, questions by id, revisions by answer id), cached on disk."""
    d = CACHE / site
    d.mkdir(parents=True, exist_ok=True)

    def cached(name: str, compute):
        f = d / f"{name}.json"
        if f.exists() and not refresh:
            return json.loads(f.read_text())
        value = compute()
        f.write_text(json.dumps(value, indent=1))
        return value

    answers = cached(f"answers-{user_id}", lambda: api_all(
        f"users/{user_id}/answers", site=site, sort="creation", order="asc"))
    print(f"{site}: {len(answers)} answers by user {user_id}")

    def get_questions():
        ids = sorted({a["question_id"] for a in answers})
        out = {}
        for batch in chunks(ids, 100):
            for q in api_all("questions/" + ";".join(map(str, batch)), site=site):
                out[str(q["question_id"])] = q
        return out
    questions = cached(f"questions-{user_id}", get_questions)

    def get_revisions():
        out: dict[str, list] = {}
        ids = [a["answer_id"] for a in answers]
        for batch in chunks(ids, 50):
            for r in api_all("posts/" + ";".join(map(str, batch)) + "/revisions", site=site):
                out.setdefault(str(r["post_id"]), []).append(r)
        return out
    revisions = cached(f"revisions-{user_id}", get_revisions)
    return answers, questions, revisions


# ---------------------------------------------------------------- markdown
FENCE_RE = re.compile(r"^(\s*)(```+|~~~+)(.*)$")
LANG_HINT_RE = re.compile(r"^\s*<!--\s*language(-all)?:\s*(?:lang-)?([\w+-]+)\s*-->\s*$")
LIST_RE = re.compile(r"^\s{0,3}([-*+]|\d+[.)])\s+\S")
# Stack Exchange / highlight.js language labels → Pandoc highlighting names
HINT_LANG = {"tex": "latex", "latex": "latex", "none": "", "default": "", "text": "",
             "plaintext": "", "shell": "bash", "sh": "bash", "console": "bash",
             "shell-session": "bash", "js": "javascript", "py": "python", "python3": "python",
             "c++": "cpp", "c#": "cs", "csharp": "cs", "objective-c": "objectivec",
             "objc": "objectivec", "ts": "typescript", "yml": "yaml", "md": "markdown"}


def normalize_code(md: str, default_lang: str) -> str:
    """Fence indented code blocks, apply <!-- language: … --> hints, and give unlabeled
    fences the site's default language. Also add the blank line Pandoc needs before a
    list that directly follows a paragraph (CommonMark doesn't need it)."""
    lines = md.split("\n")
    out: list[str] = []
    lang_all = default_lang
    next_lang: str | None = None
    in_list = False
    i = 0
    while i < len(lines):
        line = lines[i]
        m = LANG_HINT_RE.match(line)
        if m:
            lang = HINT_LANG.get(m.group(2).lower(), m.group(2).lower())
            if m.group(1):
                lang_all = lang
            else:
                next_lang = lang
            in_list = False   # an HTML comment at column 0 ends a list
            i += 1
            continue
        m = FENCE_RE.match(line)
        if m:  # copy fenced block verbatim, adding a language if it has none
            indent, fence, info = m.groups()
            lang = next_lang if next_lang is not None else lang_all
            label = info.strip().removeprefix("lang-")
            if not label and lang:
                info = lang
            elif re.fullmatch(r"[\w+#.-]+", label):
                info = HINT_LANG.get(label.lower(), label)
            elif re.fullmatch(r"\{[^{}=][^{}]*\}", label):
                info = "{" + label + "}"   # {r} would be executed by Quarto; {{r}} is shown as-is
            out.append(f"{indent}{fence}{info}")
            i += 1
            while i < len(lines):
                out.append(lines[i])
                if lines[i].strip().startswith(fence[0] * len(fence)) and \
                        lines[i].strip().strip(fence[0]) == "":
                    i += 1
                    break
                i += 1
            next_lang = None
            continue
        prev_blank = not out or not out[-1].strip()
        if line.startswith("    ") and line.strip() and prev_blank and not in_list:
            block = []
            while i < len(lines) and (lines[i].startswith("    ") or not lines[i].strip()):
                block.append(lines[i][4:] if lines[i].strip() else "")
                i += 1
            while block and not block[-1].strip():
                block.pop()
                i -= 1
            lang = next_lang if next_lang is not None else lang_all
            out += ["```" + lang] + block + ["```"]
            next_lang = None
            continue
        if prev_blank and re.fullmatch(r" {0,3}(-[ \t]*){3,}", line):
            # a `---` rule can be mistaken for a YAML block by Pandoc
            out.append("* * *")
            i += 1
            continue
        if line.strip():
            if LIST_RE.match(line):
                if not prev_blank and not in_list and out and not out[-1].lstrip().startswith(">"):
                    out.append("")
                in_list = True
            elif not line.startswith(" ") and prev_blank:
                in_list = False
        out.append(line)
        i += 1
    return "\n".join(out)


def split_code(md: str) -> list[tuple[bool, str]]:
    """Split into (is_code, text) segments: fenced blocks and inline code spans."""
    segs: list[tuple[bool, str]] = []
    text: list[str] = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        m = FENCE_RE.match(lines[i])
        if m:
            fence = m.group(2)
            block = [lines[i]]
            i += 1
            while i < len(lines):
                block.append(lines[i])
                i += 1
                if lines[i - 1].strip().startswith(fence) and lines[i - 1].strip().strip(fence[0]) == "":
                    break
            segs.append((False, "\n".join(text) + "\n"))
            text = []
            segs.append((True, "\n".join(block) + "\n"))
            continue
        text.append(lines[i])
        i += 1
    segs.append((False, "\n".join(text)))
    out: list[tuple[bool, str]] = []
    for is_code, s in segs:
        if is_code:
            out.append((True, s))
            continue
        pos = 0
        for m in re.finditer(r"(`+)(?!`).+?(?<!`)\1(?!`)", s, re.S):
            out.append((False, s[pos:m.start()]))
            out.append((True, m.group(0)))
            pos = m.end()
        out.append((False, s[pos:]))
    return out


ENV_RE = re.compile(r"(?<!\$)(\\begin\{(align|aligned|equation|gather|multline|eqnarray|"
                    r"alignat|array|cases|split)\*?\}.*?\\end\{\2\*?\})(?!\$)", re.S)


def fix_math(text: str) -> str:
    """Math.SE (MathJax) → Pandoc: wrap bare environments in $$, trim spaces just inside
    inline $…$ (Pandoc won't treat `$ x $` as math), and protect math from Markdown."""
    def wrap_env(s: str) -> str:
        # only environments that aren't already inside $$ … $$
        parts = re.split(r"(\$\$.*?\$\$)", s, flags=re.S)
        return "".join(p if p.startswith("$$") else ENV_RE.sub(r"$$\1$$", p) for p in parts)
    text = wrap_env(text)
    out, pos = [], 0
    for m in re.finditer(r"\$\$(.+?)\$\$|(?<![\\$])\$(?!\$)((?:\\.|[^$\\])+?)\$", text, re.S):
        out.append(text[pos:m.start()])
        if m.group(1) is not None:
            out.append("$$" + m.group(1).strip() + "$$")
        elif "\n\n" in m.group(2):
            out.append(m.group(0))   # not math: crosses a paragraph
        else:
            out.append("$" + m.group(2).strip() + "$")
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def escape_dollars(text: str) -> str:
    """TeX.SE doesn't render $…$ as math, so a literal $ must stay literal."""
    return re.sub(r"(?<!\\)\$", r"\\$", text)


def prefix_refs(text: str, prefix: str) -> str:
    """Rename reference-link labels ([text][1], [1]: url) so the quoted question's
    references don't collide with the answer's (both usually number from 1)."""
    text = re.sub(r"^( {0,3})\[([^\]]+)\]:", rf"\1[{prefix}\2]:", text, flags=re.M)
    return re.sub(r"\]\[([^\]]+)\]", rf"][{prefix}\1]", text)


def convert(md: str, site: str, ref_prefix: str = "", code_lang: str | None = None) -> str:
    info = SITES[site]
    md = html.unescape(md).replace("\r\n", "\n")
    md = normalize_code(md, info["code_lang"] if code_lang is None else code_lang)
    segs = []
    for is_code, s in split_code(md):
        if not is_code:
            s = fix_math(s) if info["mathjax"] else escape_dollars(s)
            s = s.replace("{{<", "{{</*").replace(">}}", "*/>}}")
            if ref_prefix:
                s = prefix_refs(s, ref_prefix)
        segs.append(s)
    return "".join(segs).strip() + "\n"


def plain_summary(md: str, limit: int = 160) -> str:
    for para in re.split(r"\n\s*\n", md):
        p = para.strip()
        if not p or p.startswith(("```", "    ", "![", "<", "#", "|", ">", "[")) and \
                not re.match(r"\[[^\]]+\]\(", p):
            continue
        p = re.sub(r"!\[[^\]]*\]\[?[^\]\)]*[\]\)]", "", p)
        p = re.sub(r"\[([^\]]+)\](\([^)]*\)|\[[^\]]*\])", r"\1", p)
        p = re.sub(r"[*_`]+", "", p)
        p = re.sub(r"\\([$])", r"\1", p)
        p = re.sub(r"\s+", " ", p).strip()
        if len(p) < 20:
            continue
        if len(p) > limit:
            p = p[:limit].rsplit(" ", 1)[0].rstrip(",;:") + "…"
        return p
    return ""


# ---------------------------------------------------------------- images & links
IMG_URL_RE = re.compile(r"https?://(?:%s)/[\w./-]+" % "|".join(map(re.escape, IMAGE_HOSTS)))


def localize_images(md: str, post_dir: Path) -> str:
    def fetch(m: re.Match) -> str:
        url = m.group(0)
        name = url.rsplit("/", 1)[-1].split("?")[0]
        target = post_dir / name
        if not target.exists():
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=60) as r:
                    target.write_bytes(r.read())
            except (urllib.error.URLError, OSError) as e:
                print(f"  WARNING: couldn't download {url}: {e}", file=sys.stderr)
                return url
        return name
    return IMG_URL_RE.sub(fetch, md)


ANSWER_URL_RE = re.compile(
    r"https?://([\w.-]+\.(?:com|net))/(?:a/(\d+)(?:/\d+)?|questions/\d+/[^/\s)#]*/(\d+)(?:#\d+)?)")


def read_front(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, text


def relink(posts: dict[str, Path]) -> int:
    """Point links to my other answers at their local post, once that post is published."""
    published = {}
    for key, path in posts.items():
        front, _ = read_front(path / "index.qmd")
        if path.parent == PUBLISHED and not front.get("draft"):
            published[key] = f"/blog/answers/{path.name}/"
    host_site = {info["host"]: site for site, info in SITES.items()}
    changed = 0
    for key, path in posts.items():
        f = path / "index.qmd"
        _, text = read_front(f)

        def sub(m: re.Match) -> str:
            if m.group(1) not in host_site:
                return m.group(0)
            k = f"{host_site[m.group(1)]}/{m.group(2) or m.group(3)}"
            if k == key or k not in published:
                return m.group(0)
            return published[k]
        # leave the attribution footer alone (it links to this post's own original)
        head, sep, foot = text.partition("\n::: {.se-attribution")
        new = ANSWER_URL_RE.sub(sub, head) + sep + foot
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed += 1
    return changed


# ---------------------------------------------------------------- post
def date_of(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def license_of(post: dict) -> str:
    if post.get("content_license"):
        return post["content_license"]
    d = date_of(post["creation_date"])
    return "CC BY-SA 2.5" if d < "2011-04-08" else "CC BY-SA 3.0" if d < "2018-05-02" else "CC BY-SA 4.0"


def license_link(lic: str) -> str:
    ver = lic.rsplit(" ", 1)[-1]
    return f"[{lic}](https://creativecommons.org/licenses/by-sa/{ver}/)"


def user_link(u: dict | None) -> str:
    if not u:
        return "an anonymous user"
    name = html.unescape(u.get("display_name", "a deleted user"))
    return f"[{name}]({u['link']})" if u.get("link") else name


def other_editors(answer: dict, revs: list[dict]) -> list[dict]:
    me = answer["owner"].get("user_id")
    seen, out = set(), []
    for r in sorted(revs, key=lambda r: r["creation_date"]):
        u = r.get("user") or {}
        uid = u.get("user_id")
        if uid in (None, me, -1) or uid in seen:   # -1 is the Community bot
            continue
        seen.add(uid)
        out.append(u)
    return out


def slug_of(answer: dict) -> str:
    m = re.search(r"/questions/\d+/([^/]+)/", answer["link"])
    slug = m.group(1) if m else str(answer["answer_id"])
    return slug[:60].rstrip("-")


def build_post(site: str, a: dict, q: dict | None, revs: list[dict], post_dir: Path) -> str:
    info = SITES[site]
    title = html.unescape(a.get("title") or (q or {}).get("title") or slug_of(a))
    if not info["mathjax"]:
        title = escape_dollars(title)
    tags = (q or {}).get("tags", [])
    lang = code_lang_for(site, tags)
    body = localize_images(convert(a["body_markdown"], site, code_lang=lang), post_dir)
    answer_date = date_of(a["creation_date"])
    lic = license_of(a)

    front = {
        "title": title,
        "date": answer_date,
        "description": plain_summary(body),
        # Only the site as a category: hundreds of SE tags would swamp the
        # Writing page's category list. Promote tags to categories by hand if wanted.
        "categories": [info["category"]],
        "license": lic,
        "draft": True,
        "se-site": site,
        "se-answer-id": a["answer_id"],
        "se-link": a["link"],
        "se-score": a["score"],
        "se-accepted": bool(a.get("is_accepted")),
        "se-tags": tags,
    }

    parts = ["<!-- Imported from %s by tools/import_stackexchange.py. Trim or paraphrase\n"
             "     the quoted question, expand the answer, then delete `draft: true`. -->\n"
             % info["short"]]
    if q:
        qbody = localize_images(convert(q["body_markdown"], site, ref_prefix="q-", code_lang=lang), post_dir)
        quoted = "\n".join(("> " + ln) if ln.strip() else ">" for ln in qbody.rstrip().split("\n"))
        collapse = ' collapse="true"' if len(qbody) > LONG_QUESTION else ""
        parts.append(
            f'::: {{.callout-note .se-question appearance="simple"{collapse}}}\n'
            f"## The question\n\n"
            f"[{title}]({q['link']}), asked by {user_link(q.get('owner'))} on "
            f"{info['name']} ({date_of(q['creation_date'])}; {license_link(license_of(q))}):\n\n"
            f"{quoted}\n:::\n")
    parts.append(body)

    editors = other_editors(a, revs)
    edits = ""
    if editors:
        names = ", ".join(user_link(u) for u in editors)
        rev_url = f"https://{info['host']}/posts/{a['answer_id']}/revisions"
        edits = f", with [edits]({rev_url}) by {names}"
    parts.append(
        f'::: {{.se-attribution}}\n'
        f"Originally posted as [an answer]({a['link']}) on {info['name']}, "
        f"{answer_date}{edits}. Licensed {license_link(lic)}.\n:::\n")

    return ("---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True, width=1000)
            + "---\n\n" + "\n".join(parts))


# ---------------------------------------------------------------- main
def load_site(param: str, refresh: bool = False) -> bool:
    """Add a site to SITES from the API's list of Stack Exchange sites (cached)."""
    f = CACHE / "sites.json"
    if f.exists() and not refresh:
        sites = json.loads(f.read_text())
    else:
        CACHE.mkdir(parents=True, exist_ok=True)
        sites = api_all("sites")
        f.write_text(json.dumps(sites, indent=1))
    by_param = {x["api_site_parameter"]: x for x in sites}
    by_host = {urllib.parse.urlparse(x["site_url"]).netloc: x for x in sites}
    x = by_param.get(param) or by_host.get(param) or by_host.get(f"{param}.stackexchange.com")
    if not x:
        return False
    host = urllib.parse.urlparse(x["site_url"]).netloc
    name = html.unescape(x["name"])
    if host.endswith(".stackexchange.com"):
        sub = host.split(".")[0]
        info = dict(name=f"{name} Stack Exchange", short=f"{name}.SE", category=f"{sub}.se")
    else:   # stackoverflow.com, mathoverflow.net, superuser.com, …
        info = dict(name=name, short=name, category=x["api_site_parameter"].split(".")[0])
    info.update(host=host, code_lang="",
                mathjax="MathJax" in (x.get("markdown_extensions") or []))
    SITES[x["api_site_parameter"]] = info
    if x["api_site_parameter"] != param:
        SITE_ALIASES[param] = x["api_site_parameter"]
    return True


def parse_site(s: str, refresh: bool = False) -> str:
    s = SITE_ALIASES.get(s, s)
    if s not in SITES and load_site(s, refresh):
        s = SITE_ALIASES.get(s, s)
    if s not in SITES:
        raise SystemExit(f"unknown site {s!r}: use the site's API name, e.g. math, tex, "
                         "stackoverflow, academia, mathoverflow.net")
    return s


def existing_posts() -> dict[str, Path]:
    found = {}
    for d in (DRAFTS, PUBLISHED):
        for f in d.glob("*/index.qmd") if d.exists() else []:
            front, _ = read_front(f)
            if front.get("se-site") and front.get("se-answer-id"):
                found[f"{front['se-site']}/{front['se-answer-id']}"] = f.parent
    return found


def publish(paths: list[str]) -> int:
    """Move draft folders into the site and drop their `draft: true` line."""
    for p in paths:
        src = Path(p)
        if src.name == "index.qmd":
            src = src.parent
        if not src.is_absolute():
            src = (Path.cwd() / src).resolve()
        if not (src / "index.qmd").exists():
            src = DRAFTS / src.name   # allow a bare folder name
        if src.parent != DRAFTS or not (src / "index.qmd").exists():
            print(f"not a draft: {p} (expected drafts/answers/<folder>)", file=sys.stderr)
            return 1
        dest = PUBLISHED / src.name
        if dest.exists():
            print(f"already exists: {dest.relative_to(ROOT)}", file=sys.stderr)
            return 1
        moved = subprocess.run(["git", "mv", str(src), str(dest)], cwd=ROOT,
                               capture_output=True).returncode == 0
        if not moved:   # not tracked by git yet
            shutil.move(str(src), str(dest))
        f = dest / "index.qmd"
        f.write_text(re.sub(r"(?m)^draft:\s*true[^\n]*\n", "", f.read_text(encoding="utf-8"),
                            count=1), encoding="utf-8")
        print(f"published {dest.relative_to(ROOT)}")
    relink(existing_posts())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--user", action="append", default=[], metavar="SITE=ID",
                    help="e.g. math=12345 (repeatable; default: tools/stackexchange.yml)")
    ap.add_argument("--refresh", action="store_true", help="re-download from the API")
    ap.add_argument("--min-score", type=int, default=None, help="skip answers below this score")
    ap.add_argument("--only", default="", help="comma-separated answer ids to import")
    ap.add_argument("--force", default="", help="comma-separated answer ids to regenerate (overwrites)")
    ap.add_argument("--publish", nargs="+", metavar="FOLDER",
                    help="move draft folder(s) into the site and publish them (no import)")
    args = ap.parse_args()
    if args.publish:
        return publish(args.publish)

    users: dict[str, int] = {}
    if args.user:
        for u in args.user:
            site, _, uid = u.partition("=")
            users[parse_site(site.strip(), args.refresh)] = int(uid)
    elif CONFIG.exists():
        users = {parse_site(k, args.refresh): int(v)
                 for k, v in (yaml.safe_load(CONFIG.read_text()) or {}).items()}
    if not users:
        ap.error(f"no users: pass --user math=ID or create {CONFIG.relative_to(ROOT)}")

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    force = {x.strip() for x in args.force.split(",") if x.strip()}
    DRAFTS.mkdir(parents=True, exist_ok=True)
    posts = existing_posts()

    rows, created = [], 0
    for site, uid in users.items():
        answers, questions, revisions = fetch_site(site, uid, args.refresh)
        for a in answers:
            aid = str(a["answer_id"])
            key = f"{site}/{aid}"
            if only and aid not in only:
                continue
            if args.min_score is not None and a["score"] < args.min_score and key not in posts:
                continue
            q = questions.get(str(a["question_id"]))
            revs = revisions.get(aid, [])
            if key in posts and aid not in force:
                status, post_dir = "existing", posts[key]
            else:
                post_dir = posts.get(key)
                if post_dir is None:
                    name = f"{date_of(a['creation_date'])}-{site}-{slug_of(a)}"
                    post_dir = DRAFTS / name
                    if post_dir.exists() or (PUBLISHED / name).exists():   # another answer to the same question, same day
                        post_dir = post_dir.with_name(f"{post_dir.name}-{aid}")
                post_dir.mkdir(exist_ok=True)
                (post_dir / "index.qmd").write_text(build_post(site, a, q, revs, post_dir),
                                                    encoding="utf-8")
                status = "regenerated" if key in posts else "new"
                posts[key] = post_dir
                created += 1
            front, _ = read_front(post_dir / "index.qmd")
            rows.append(dict(
                site=site, date=date_of(a["creation_date"]), score=a["score"],
                accepted="yes" if a.get("is_accepted") else "",
                published="yes" if post_dir.parent == PUBLISHED and not front.get("draft") else "",
                title=html.unescape(a.get("title", "")),
                edited_by_others=", ".join(html.unescape(u.get("display_name", ""))
                                           for u in other_editors(a, revs)),
                status=status, folder=post_dir.relative_to(ROOT).as_posix(), link=a["link"]))

    rows.sort(key=lambda r: (-r["score"], r["date"]))
    if rows:
        with MANIFEST.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    relinked = relink(posts)
    print(f"{created} posts written to {DRAFTS.relative_to(ROOT)}, {len(rows) - created} already there"
          f"; {relinked} posts relinked. Manifest: {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
