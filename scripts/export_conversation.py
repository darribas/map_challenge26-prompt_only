"""Export the Claude Code conversation behind this project into a clean, publishable form.

Claude Code stores each session as a JSON Lines file under ~/.claude/projects/<project>/<session-id>.jsonl. That file is
large (images are embedded) and full of internal bookkeeping, and it lives outside the repository. This script keeps only
what a reader needs and writes it to `conversation/`:

- `conversation/conversation.json`: an ordered list of events (prompts, replies, tool calls, the context summary);
- `conversation/img/`: every image in the conversation (the user's attachments and the figures Claude looked at), as JPEGs.

What is left out: Claude's internal reasoning ("thinking" blocks), system reminders and other injected context, and
bookkeeping records. Tool inputs and outputs are kept but truncated. The user's email address is redacted.

You only need this script to refresh the conversation from a new session file; the exported files are committed.

    python scripts/export_conversation.py ~/.claude/projects/-home-jovyan-work/63c88aa3-98ca-4f27-93e3-d7a0c2754006.jsonl
"""
import argparse
import base64
import io
import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "conversation"
MAX_CHARS, MAX_LINES = 2500, 40  # truncation for tool inputs and outputs
IMG_WIDTH = 1100

REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
# Machine-specific paths, shortened to what a reader of the repository would recognise
PATHS = [(re.compile(r"/tmp/claude-\d+/[^/\s]+/[0-9a-f-]{36}/scratchpad/?"), "scratchpad/"),
         (re.compile(r"/home/jovyan/work/?"), ""),
         (re.compile(r"/home/jovyan"), "~")]


def clean(text):
    text = REMINDER.sub("", text or "")
    text = EMAIL.sub("[email redacted]", text)
    for pattern, short in PATHS:
        text = pattern.sub(short, text)
    return text.strip()


def truncate(text, max_chars=MAX_CHARS, max_lines=MAX_LINES):
    lines = text.splitlines()
    cut = "\n".join(lines[:max_lines])[:max_chars]
    return cut + ("\n[… truncated]" if len(cut) < len(text) else "")


def save_image(source, n):
    """Decode a base64 image block, shrink it and save it as conversation/img/NNN.jpg. Returns the relative path."""
    img = Image.open(io.BytesIO(base64.b64decode(source["data"]))).convert("RGB")
    if img.width > IMG_WIDTH:
        img = img.resize((IMG_WIDTH, round(img.height * IMG_WIDTH / img.width)), Image.LANCZOS)
    path = OUT / "img" / f"{n:03d}.jpg"
    img.save(path, quality=82, optimize=True)
    return path.relative_to(ROOT).as_posix()


def describe_tool(name, inp):
    """A one-line label and a short body for a tool call."""
    if name == "Bash":
        return inp.get("description") or "Run a shell command", inp.get("command", "")
    if name in ("Read", "Write", "Edit"):
        body = inp.get("content") or inp.get("new_string") or ""
        return f"{name} {inp.get('file_path', '')}", body
    if name == "SendUserFile":
        return "Send files to the user", "\n".join(inp.get("files", [])) + (f"\n\n{inp['caption']}" if inp.get("caption") else "")
    return name, json.dumps(inp, indent=1)


def main(jsonl):
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    for old in (OUT / "img").glob("*.jpg"):
        old.unlink()
    rows = [json.loads(line) for line in open(jsonl)]
    events, tools, seen, n_img, n_prompt = [], {}, set(), 0, 0
    last_read = {}  # file path -> image of the latest Read of it, so files sent to the user can show a picture

    def add_prompt(ts, text, images=(), midturn=False):
        nonlocal n_prompt
        text = clean(text)
        if text.startswith("[Image: original"):  # the harness's note on an image Claude viewed, not something typed
            text = ""
        if text.startswith("[Request interrupted by user"):
            events.append(dict(kind="interrupt", ts=ts))
            return
        if not text and not images:
            return
        n_prompt += 1
        events.append(dict(kind="prompt", n=n_prompt, ts=ts, text=text, images=list(images), midturn=midturn))

    for r in rows:
        if r.get("isSidechain"):
            continue
        ts = r.get("timestamp")
        if r.get("type") == "attachment" and r["attachment"].get("type") == "queued_command":
            add_prompt(ts, r["attachment"]["prompt"], midturn=True)  # typed while Claude was working
            continue
        if r.get("type") not in ("user", "assistant"):
            continue
        content = r["message"]["content"]
        if r["type"] == "user":
            if r.get("isCompactSummary"):
                events.append(dict(kind="compact", ts=ts, text=clean(content if isinstance(content, str) else content[0]["text"])))
                continue
            if isinstance(content, str):
                text = clean(content)
                if text and not text.startswith("<"):
                    add_prompt(ts, text)
                continue
            texts = [clean(b.get("text", "")) for b in content if b.get("type") == "text"]
            images = []
            for b in content:
                if b.get("type") == "image":
                    n_img += 1
                    images.append(save_image(b["source"], n_img))
                elif b.get("type") == "tool_result" and b.get("tool_use_id") in tools:
                    tool = tools[b["tool_use_id"]]
                    parts = b["content"] if isinstance(b["content"], list) else [{"type": "text", "text": b["content"]}]
                    out = "\n".join(clean(p.get("text", "")) for p in parts if p.get("type") == "text")
                    tool["result"] = truncate(out)
                    tool["error"] = bool(b.get("is_error"))
                    for p in parts:
                        if p.get("type") == "image":
                            n_img += 1
                            tool["images"].append(save_image(p["source"], n_img))
                    if tool["name"] == "Read" and tool["images"]:
                        last_read[tool["path"]] = tool["images"][-1]
            text = "\n".join(t for t in texts if t and not t.startswith("<"))
            if text or images:
                add_prompt(ts, text, images)
            continue
        for b in content:  # assistant
            key = (r["message"].get("id"), b.get("id") or b.get("text", "")[:200])
            if key in seen:
                continue
            seen.add(key)
            if b.get("type") == "text" and clean(b["text"]):
                events.append(dict(kind="reply", ts=ts, text=clean(b["text"])))
            elif b.get("type") == "tool_use":
                label, body = describe_tool(b["name"], b.get("input", {}))
                tool = dict(kind="tool", ts=ts, name=b["name"], label=clean(label), input=truncate(clean(body)),
                            result="", error=False, images=[], path=b.get("input", {}).get("file_path", ""),
                            sent=[])
                if b["name"] == "SendUserFile":
                    files = b["input"].get("files", [])
                    tool["sent"] = [dict(file=f, image=last_read.get(f, "")) for f in files]
                tools[b["id"]] = tool
                events.append(tool)
    (OUT / "conversation.json").write_text(json.dumps(events, indent=1, ensure_ascii=False))
    counts = {k: sum(e["kind"] == k for e in events) for k in ("prompt", "reply", "tool", "compact")}
    print(f"{len(events)} events {counts}, {n_img} images -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("jsonl", help="Claude Code session file (~/.claude/projects/<project>/<session>.jsonl)")
    main(parser.parse_args().jsonl)
