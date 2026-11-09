#!/usr/bin/env python3
"""Split Markdown into units of <=2,000 chars and batches of <=100 units.

Usage: python3 -I split_chunks.py [file.md] [--max-chars 2000] [--max-blocks 100]
Reads stdin when no file is given. Prints JSON: {"units": N, "batches": [[...], ...]}.
Stdlib only, no network. Fenced code, <callout> and $$ blocks are never split
at a blank line; an oversized fence is split on line boundaries and re-fenced, an oversized callout/toggle
is split inside and re-wrapped, and a long table repeats its header in each piece.
"""
import json
import re
import sys


def units(text):
    """Group lines into top-level units separated by blank lines outside fences/callouts/$$."""
    out, cur, fence, depth, eq = [], [], None, 0, False
    for line in text.split("\n"):
        s = line.strip()
        if fence is None and s.startswith("```"):
            fence = s[:3]
        elif fence is not None and s.startswith(fence):
            fence = None
        elif fence is None:
            if s == "$$":
                eq = not eq
            depth += len(re.findall(r"<(?:callout|toggle|columns|synced-block)\b", s))
            depth -= len(re.findall(r"</(?:callout|toggle|columns|synced-block)>", s))
        if not s and fence is None and depth <= 0 and not eq:
            if cur:
                out.append("\n".join(cur))
                cur = []
            continue
        cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


WRAP = re.compile(r"^(<(callout|toggle|synced-block)\b[^>]*>)\n?(.*?)\n?</\2>$", re.S)


def split_text(unit, limit):
    """Split one oversized unit at line, then sentence, then hard boundaries.
    Tag-wrapped units (callout, toggle, synced-block) are split on the inner body and each piece is re-wrapped;
    pipe tables repeat their header and separator rows in every piece."""
    if len(unit) <= limit:
        return [unit]
    m = WRAP.match(unit.strip())
    if m:
        open_tag, name, inner = m.group(1), m.group(2), m.group(3)
        close = f"</{name}>"
        room = limit - len(open_tag) - len(close) - 2
        return [f"{open_tag}\n{p}\n{close}" for p in split_text(inner, room)]
    rows = unit.split("\n")
    if len(rows) > 2 and rows[0].lstrip().startswith("|") and re.match(r"^\s*\|[\s:|-]+\|\s*$", rows[1]):
        head, out, cur = rows[:2], [], []
        base = len("\n".join(head))
        for r in rows[2:]:
            if cur and base + sum(len(x) + 1 for x in cur) + len(r) + 1 > limit:
                out.append("\n".join(head + cur)); cur = []
            cur.append(r)
        if cur: out.append("\n".join(head + cur))
        return out
    lines = unit.split("\n")
    fence = lines[0].strip()[:3] if lines[0].strip().startswith("```") else None
    lang = lines[0].strip() if fence else ""
    body = lines[1:-1] if fence and len(lines) > 1 and lines[-1].strip().startswith("```") else lines
    budget = limit - (len(lang) + 5 if fence else 0)
    pieces, cur = [], ""
    for ln in body:
        sep = "\n" if fence or len(ln) <= budget else " "
        parts = [ln]
        if len(ln) > budget:  # sentence split, then hard split
            parts = re.split(r"(?<=[.!?])\s+", ln)
            parts = [p[i:i + budget] for p in parts for i in range(0, max(len(p), 1), budget)]
        for p in parts:
            if cur and len(cur) + len(p) + 1 > budget:
                pieces.append(cur)
                cur = p
            else:
                cur = f"{cur}{sep}{p}" if cur else p
    if cur:
        pieces.append(cur)
    return [f"{lang}\n{p}\n```" for p in pieces] if fence else pieces


def main(argv):
    limit, nmax, path, i = 2000, 100, None, 0
    while i < len(argv):
        if argv[i] == "--max-chars":
            limit = int(argv[i + 1]); i += 2
        elif argv[i] == "--max-blocks":
            nmax = int(argv[i + 1]); i += 2
        else:
            path = argv[i]; i += 1
    text = open(path, encoding="utf-8").read() if path else sys.stdin.read()
    flat = [p for u in units(text) for p in split_text(u, limit)]
    batches = [flat[k:k + nmax] for k in range(0, len(flat), nmax)]
    json.dump({"units": len(flat), "batches": batches}, sys.stdout, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main(sys.argv[1:])
