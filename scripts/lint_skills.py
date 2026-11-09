#!/usr/bin/env python3
"""Lint every skills/*/*/SKILL.md against the repo rules. Stdlib only. Usage: python3 -I scripts/lint_skills.py"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECTIONS = ["Purpose", "Activation triggers", "Required tools", "Dependencies", "Operating principles",
            "Detailed workflow", "Implementation instructions", "Examples", "Validation checklist",
            "Failure handling", "Safety constraints"]
LABELS = ("API-supported", "MCP-supported", "UI-only", "external")
SECRET = re.compile(r"(secret_[A-Za-z0-9]{20,}|ntn_[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{20,}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
LINK = re.compile(r"\]\((?!https?:|#|mailto:)([^)\s]+)\)")

def check(path):
    errs, warns = [], []
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    skill_dir = os.path.basename(os.path.dirname(path))
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m: return ["missing frontmatter"], warns
    fm = dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M))
    if set(fm) != {"name", "description"}: errs.append(f"frontmatter keys must be exactly name,description (got {sorted(fm)})")
    if fm.get("name") != skill_dir: errs.append(f"name '{fm.get('name')}' != folder '{skill_dir}'")
    if len(fm.get("description", "")) < 40: errs.append("description too short to trigger on")
    heads = [h.strip() for h in re.findall(r"^## (.+)$", text, re.M)]
    pos = [heads.index(s) if s in heads else -1 for s in SECTIONS]
    for s, p in zip(SECTIONS, pos):
        if p < 0: errs.append(f"missing section: {s}")
    present = [p for p in pos if p >= 0]
    if present != sorted(present): errs.append("required sections are out of order")
    n = len(lines)
    if not 90 <= n <= 200: warns.append(f"{n} lines (target 90-200)")
    for link in LINK.findall(text):
        target = os.path.normpath(os.path.join(os.path.dirname(path), link.split("#")[0]))
        if link.split("#")[0] and not os.path.exists(target): errs.append(f"broken link: {link}")
    # strip fenced code before secret scan? no: secrets are wrong anywhere. UUIDs allowed only as <PLACEHOLDER> forms
    for mm in SECRET.finditer(text):
        errs.append(f"possible secret or real ID: {mm.group(0)[:12]}...")
    if not any(l in text for l in LABELS): errs.append("no capability labels (API-supported/MCP-supported/UI-only/external)")
    if re.search(r"^## Detailed workflow", text, re.M):
        wf = text.split("## Detailed workflow", 1)[1].split("\n## ", 1)[0].lower()
        touches = not any(k in skill_dir for k in ("auditor",))
        if touches and not all(k in wf for k in ("analyze", "retrieve", "plan", "payload", "execute", "verify", "report")):
            warns.append("workflow does not show all 7 protocol steps (analyze/retrieve/plan/payload/execute/verify/report)")
    return errs, warns

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "skills", "*", "*", "SKILL.md")))
    bad = 0
    for f in files:
        errs, warns = check(f)
        rel = os.path.relpath(f, ROOT)
        status = "FAIL" if errs else ("WARN" if warns else "OK")
        print(f"{status:4} {rel}")
        for e in errs: print("     error:", e)
        for w in warns: print("     warn: ", w)
        bad += bool(errs)
    print(f"\n{len(files)} skills, {bad} with errors")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
