"""Prepare everything the Quarto site needs that is generated rather than written by hand.

Run it from the repository root before `quarto render`:

    python scripts/build_site.py

It needs only Pillow, and reads files that are in the repository (no data files needed):

1. Web images: every PNG under `figures/` is copied to `images/` as a smaller JPEG (the originals are 200 dpi and
   up to 3 MB each).
2. From `conversation/conversation.json` (made by `export_conversation.py`) it writes, under `_generated/`:
   - `transcript.md`: the full conversation, day by day, with every prompt anchored as `#p-N`;
   - `prompts.md`: every prompt the human typed, as typed notes linking back to the transcript;
   - `prompt-N.md`: one snippet per prompt, so other pages can quote a prompt verbatim with
     `{{< include _generated/prompt-N.md >}}`;
3. `_variables.yml`: counts used in the text (`{{< var n_prompts >}}` and so on);
4. `_generated/log.md`: `LOG.md` without its top-level title, for the Log page.
"""
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "_generated"
WEB_WIDTH = 1400


def web_images():
    """figures/**/*.png -> images/**/*.jpg, skipping files that are already up to date."""
    n = 0
    for src in sorted((ROOT / "figures").rglob("*.png")):
        dst = ROOT / "images" / src.relative_to(ROOT / "figures").with_suffix(".jpg")
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        img = Image.open(src).convert("RGB")
        if img.width > WEB_WIDTH:
            img = img.resize((WEB_WIDTH, round(img.height * WEB_WIDTH / img.width)), Image.LANCZOS)
        img.save(dst, quality=85, optimize=True)
        n += 1
    print(f"web images: {n} updated")


def when(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def esc(text):
    return html.escape(text).replace("\n", "<br>")


def note(e, link=None):
    """A prompt as a typed note. `link` points the number at another page (the transcript) instead of itself."""
    t = when(e["ts"])
    href = link or f"#p-{e['n']}"
    extra = " · typed while Claude was working" if e["midturn"] else ""
    imgs = "".join(f'<img src="{p}" alt="Image attached to prompt {e["n"]}" loading="lazy">' for p in e["images"])
    anchor = "" if link else f' id="p-{e["n"]}"'
    return (f'<div class="note prompt"{anchor}><div class="note-meta"><a href="{href}">#{e["n"]}</a> · '
            f'{t:%a} {t.day} {t:%b, %H:%M}{extra}</div><div class="note-text">{esc(e["text"])}</div>{imgs}</div>')


def raw(block):
    """Wrap HTML so pandoc passes it through untouched; the fence must be longer than any backtick run inside."""
    fence = "`" * max(3, max((len(m) for m in re.findall(r"`+", block)), default=0) + 1)
    return f"\n{fence}{{=html}}\n{block}\n{fence}\n"


def demote(md):
    """Make a reply safe to nest in the page: headings become bold lines (so they stay out of the table of contents),
    and a blank line goes before any list or table that follows a line of text, which pandoc needs to see it."""
    md = re.sub(r"^#{1,6}\s+(.*)$", r"**\1**", md, flags=re.M)
    return re.sub(r"(?m)^(\S(?![-*] |\d+\. ).*)\n(?=[ \t]*(?:[-*] |\d+\. |\|))", r"\1\n\n", md)


def site_path(path):
    """Map a local file path from the conversation to its web copy, if the site has one."""
    m = re.search(r"(?:^|/)figures/(.+)\.png$", path)
    if m and (ROOT / "images" / f"{m.group(1)}.jpg").exists():
        return f"images/{m.group(1)}.jpg"
    return ""


def tool_html(t):
    status = ' <span class="tool-error">error</span>' if t["error"] else ""
    body = f'<pre class="tool-in">{html.escape(t["input"])}</pre>'
    if t["result"]:
        body += f'<pre class="tool-out">{html.escape(t["result"])}</pre>'
    return (f'<details class="tool"><summary><span class="tool-name">{html.escape(t["name"])}</span> '
            f'{html.escape(t["label"][:140])}{status}</summary>{body}</details>')


def figures_html(t):
    """Images that came out of a tool call: what Claude looked at, or what it sent to the user."""
    out = []
    for p in t["images"]:
        out.append(f'<figure class="seen"><img src="{p}" loading="lazy" alt="Image viewed by Claude">'
                   f'<figcaption>Claude looked at <code>{html.escape(Path(t["path"]).name)}</code></figcaption></figure>')
    sent = [s for s in t.get("sent", []) if s["image"] or site_path(s["file"])]
    if sent:
        thumbs = "".join(f'<img src="{site_path(s["file"]) or s["image"]}" loading="lazy" alt="{html.escape(Path(s["file"]).name)}">'
                         for s in sent)
        out.append(f'<figure class="sent"><div class="sent-row">{thumbs}</div>'
                   f'<figcaption>Sent to the user: {", ".join(html.escape(Path(s["file"]).name) for s in sent)}</figcaption></figure>')
    return "".join(out)


def transcript(events):
    lines = [
        "<!-- Generated by scripts/build_site.py from conversation/conversation.json. Do not edit by hand. -->",
    ]
    day, run = None, []

    def flush():
        if not run:
            return
        firsts = [t["label"].splitlines()[0][:70] for t in run[:2]]
        labels = html.escape(" · ".join(firsts)) + (" · …" if len(run) > 2 else "")
        inner = "".join(tool_html(t) for t in run)
        lines.append(raw(f'<details class="steps"><summary><b>{len(run)} step{"s" * (len(run) > 1)}</b> · {labels}</summary>'
                         f'{inner}</details>' + "".join(figures_html(t) for t in run)))
        run.clear()

    for e in events:
        d = when(e["ts"]).date()
        if d != day:
            flush()
            day = d
            lines.append(f"\n## {d:%A} {d.day} {d:%B}\n")
        if e["kind"] == "tool":
            run.append(e)
            continue
        flush()
        if e["kind"] == "prompt":
            lines.append(raw(note(e)))
        elif e["kind"] == "reply":
            lines.append(f"\n::: {{.reply}}\n{demote(e['text'])}\n:::\n")
        elif e["kind"] == "interrupt":
            lines.append(raw('<div class="interrupt">— interrupted —</div>'))
        elif e["kind"] == "compact":
            lines.append(raw(
                '<details class="compact"><summary>The conversation outgrew Claude\'s context window here. '
                'Everything above was condensed into the summary below, which is all Claude carried forward.</summary>'
                f'<div class="compact-text">{esc(e["text"])}</div></details>'))
    flush()
    (GEN / "transcript.md").write_text("\n".join(lines))


def prompts(events):
    ps = [e for e in events if e["kind"] == "prompt"]
    lines, day = [], None
    for e in ps:
        d = when(e["ts"]).date()
        if d != day:
            day = d
            lines.append(f"\n## {d:%A} {d.day} {d:%B}\n")
        lines.append(raw(note(e, link=f"transcript.html#p-{e['n']}")))
    (GEN / "prompts.md").write_text("\n".join(lines))
    for e in ps:
        (GEN / f"prompt-{e['n']}.md").write_text(raw(note(e, link=f"transcript.html#p-{e['n']}")))


def variables(events):
    ps = [e for e in events if e["kind"] == "prompt"]
    tools = [e for e in events if e["kind"] == "tool"]
    names = Counter(t["name"] for t in tools)
    days = sorted({when(e["ts"]).date() for e in events})
    words = sum(len(e["text"].split()) for e in ps)
    v = {
        "n_prompts": len(ps),
        "n_prompt_words": words,
        "n_replies": sum(e["kind"] == "reply" for e in events),
        "n_tools": len(tools),
        "n_nb": sum(t["name"] == "Bash" and t["input"].lstrip().startswith("nb ") for t in tools),
        "n_images_seen": sum(len(t["images"]) for t in tools),
        "n_sent": names["SendUserFile"],
        "n_days": len(days),
        "first_day": f"{days[0]:%d %B %Y}",
        "last_day": f"{days[-1]:%d %B %Y}",
    }
    (ROOT / "_variables.yml").write_text("".join(f"{k}: \"{val}\"\n" for k, val in v.items()))
    print("variables:", v)


if __name__ == "__main__":
    GEN.mkdir(exist_ok=True)
    for old in GEN.glob("prompt-*.md"):
        old.unlink()
    web_images()
    events = json.loads((ROOT / "conversation" / "conversation.json").read_text())
    transcript(events)
    prompts(events)
    variables(events)
    log = (ROOT / "LOG.md").read_text()
    (GEN / "log.md").write_text(re.sub(r"\A# .*\n+", "", log))
    print(f"generated: {', '.join(sorted(p.name for p in GEN.iterdir())[:4])}, … in {GEN.relative_to(ROOT)}/")
