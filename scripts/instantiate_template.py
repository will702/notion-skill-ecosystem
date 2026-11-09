#!/usr/bin/env python3
"""Instantiate a template folder (schema.json + page.md) under an explicit parent page using `ntn`.

  python3 -I scripts/instantiate_template.py templates/dashboards/project-dashboard --parent <PAGE_ID> --dry-run
  python3 -I scripts/instantiate_template.py templates/project --parent <PAGE_ID> [--seed] [--set KEY=VALUE ...]
  python3 -I scripts/instantiate_template.py --rollback <manifest.json>

Order: databases -> relations -> rollups -> formulas -> page (Markdown v2) -> linked views moved to their {{VIEW:name}} markers.
Linked-view placement is tested: create_database appends the block at the end of the page; the block is then moved by
rewriting its <database .../> tag inside a v2 update_content call (reference: references/enhanced-markdown.md).
Retries 429/529 on any method, and 5xx only on GET/DELETE (a 5xx POST/PATCH may have succeeded: re-read, do not resend). Never deletes: rollback only trashes objects listed in the manifest.
Stdlib only; every ntn call runs with stdin closed. Writes a manifest of created IDs (default ./last_manifest.json).
"""
import argparse, json, os, re, subprocess, sys, time

CALLS = {"n": 0}
DRY = False

def api(path, body=None, method=None, query=None, retries=5):
    args = ["ntn", "api", path] + (query or [])
    if body is not None: args += ["-d", json.dumps(body)]
    if method: args += ["-X", method]
    m = method or ("POST" if body is not None else "GET")
    if DRY:
        print(f"  [dry-run] {m} {path} {json.dumps(body)[:110] if body else ''}")
        return {"id": "DRY-" + str(CALLS["n"]), "data_sources": [{"id": "DRY-DS"}], "properties": {}, "results": [], "markdown": ""}
    for a in range(retries):
        time.sleep(0.4)  # stay under ~3 requests/second
        CALLS["n"] += 1
        r = subprocess.run(args, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if r.returncode == 0: return json.loads(r.stdout) if r.stdout.strip() else {}
        err = r.stderr or r.stdout
        code = re.search(r"\((4\d\d|5\d\d)[ )]", err[:600]) or re.search(r"\bHTTP (4\d\d|5\d\d)\b", err[:600]); code = code.group(1) if code else ""
        idem = m in ("GET", "DELETE")
        if code in ("429", "529") or (idem and code in ("500", "502", "503", "504")):
            time.sleep(min(2 ** a * 2, 30)); continue
        raise RuntimeError(f"{m} {path} failed ({code or 'no status'}): {err[:300]}")
    raise RuntimeError(f"{m} {path}: retries exhausted")

def clean(o):
    if isinstance(o, dict): return {k: clean(v) for k, v in o.items() if not k.startswith("_")}
    if isinstance(o, list): return [clean(v) for v in o]
    return o

def to_api(props, row):
    """Accept plain seed values ({"Name": "x", "Due Date": "2026-01-01"}) or ready API values; convert by property type."""
    out = {}
    for k, v in row.items():
        if isinstance(v, (dict, list)) and not (isinstance(v, list) and v and isinstance(v[0], str)):
            out[k] = v; continue
        t = next((t for t in props.get(k, {}) if not t.startswith("_")), None)
        if t == "title" or t == "rich_text": out[k] = {t: [{"type": "text", "text": {"content": str(v)}}]}
        elif t in ("select", "status"): out[k] = {t: {"name": str(v)}}
        elif t == "multi_select": out[k] = {t: [{"name": x} for x in (v if isinstance(v, list) else [v])]}
        elif t == "date": out[k] = {t: {"start": str(v)}}
        elif t in ("number", "checkbox", "url"): out[k] = {t: v}
        else: raise ValueError(f"cannot convert seed value for property '{k}' (type {t})")
    return out

def dbs_of(schema):
    """Normalize the three schema shapes into [{name, properties, views, formulas, seed_rows}]."""
    props = schema["properties"]
    first = next(iter(props.values()))
    multi = isinstance(first, dict) and not any(k in first for k in
        ("title", "select", "multi_select", "number", "date", "formula", "rich_text", "relation", "rollup", "checkbox", "status", "url", "people"))
    out = []
    if multi:
        for name, p in props.items():
            out.append({"name": name, "properties": p,
                "views": [v for v in schema.get("views", []) if v.get("database") == name],
                "formulas": {f["property"]: f["expression"] for f in schema.get("formulas", []) if f.get("database") == name},
                "seed_rows": [r["properties"] for r in schema.get("seed_rows", []) if r.get("database") == name]})
    else:
        f = schema.get("formulas", {})
        if isinstance(f, list): f = {x["property"]: x["expression"] for x in f}
        out.append({"name": schema["title"], "properties": props, "views": schema.get("views", []), "formulas": f, "seed_rows": schema.get("seed_rows", [])})
        for extra in ("areas_database", "sources_database"):
            if extra in schema:
                e = schema[extra]; out.insert(0, {"name": e["title"], "properties": e["properties"], "views": [], "formulas": {}, "seed_rows": []})
    return out

def main():
    global DRY
    ap = argparse.ArgumentParser()
    ap.add_argument("template", nargs="?")
    ap.add_argument("--parent"); ap.add_argument("--dry-run", action="store_true"); ap.add_argument("--seed", action="store_true")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE"); ap.add_argument("--manifest", help="default: manifest-<template>-<timestamp>.json")
    ap.add_argument("--rollback")
    a = ap.parse_args(); DRY = a.dry_run
    if a.rollback:
        man = json.load(open(a.rollback)); failed = []
        print("rolling back (trash, recoverable) objects listed in", a.rollback, "for parent", man["parent"])
        for kind, i in reversed(man["created"]):
            path = f"v1/{'databases' if kind == 'database' else 'pages'}/{i}"
            try: api(path, {"in_trash": True}, "PATCH"); print("trashed", kind, i)
            except RuntimeError as e: failed.append(i); print("FAILED", kind, i, str(e)[:120])
        print(f"rollback done, {len(failed)} failed (re-run is safe: trashing is idempotent)"); return
    if not a.template or not a.parent: ap.error("template and --parent are required")
    subs = dict(s.split("=", 1) for s in a.set)
    tdir = a.template
    schema = json.load(open(os.path.join(tdir, "schema.json"))) if os.path.exists(os.path.join(tdir, "schema.json")) else None
    page_md = open(os.path.join(tdir, "page.md")).read() if os.path.exists(os.path.join(tdir, "page.md")) else None
    created, report = [], []
    if not a.manifest:
        a.manifest = f"manifest-{os.path.basename(os.path.normpath(a.template))}-{time.strftime('%Y%m%d-%H%M%S')}.json"
    if not DRY and os.path.exists(a.manifest): ap.error(f"{a.manifest} exists; choose another --manifest (never overwritten)")
    def track(kind, i):
        created.append((kind, i))
        if not DRY: json.dump({"parent": a.parent, "template": tdir, "created": created}, open(a.manifest, "w"), indent=1)
    parent = {"type": "page_id", "page_id": a.parent}
    ds_of, db_of, spec = {}, {}, []
    if schema:
        spec = dbs_of(schema)
        # 1. databases with plain properties only
        for d in spec:
            plain = {k: clean(v) for k, v in d["properties"].items() if not any(t in v for t in ("relation", "rollup", "formula"))}
            r = api("v1/databases", {"parent": parent, "title": [{"type": "text", "text": {"content": d["name"]}}], "initial_data_source": {"properties": plain}})
            db_of[d["name"]] = r["id"]; ds_of[d["name"]] = r["data_sources"][0]["id"]; track("database", r["id"]); print("database", d["name"], r["id"])
        key = lambda n: re.sub(r"[^A-Z0-9]+", "_", n.upper()).strip("_")
        lookup = {key(n): ds for n, ds in ds_of.items()}
        def resolve(o):
            s = json.dumps(o)
            def sub(m):
                name = m.group(1) or m.group(2)
                return lookup.get(name) or subs.get(name + "_DS_ID") or m.group(0)
            s = re.sub(r"\{\{([A-Z0-9_]+?)_DS_ID\}\}|<([A-Z0-9_]+?)_DATA_SOURCE_ID>", sub, s)
            return json.loads(s)
        # 2. relations, 3. rollups
        for kind in ("relation", "rollup"):
            for d in spec:
                for n, p in d["properties"].items():
                    if kind in p:
                        body = resolve(clean(p))
                        if re.search(r"\{\{[A-Z0-9_]+_DS_ID\}\}|<[A-Z0-9_]+_DATA_SOURCE_ID>", json.dumps(body)):
                            report.append(f"skipped {kind} {d['name']}.{n}: target data source not in template (pass --set <NAME>_DS_ID=<id>)"); continue
                        if kind == "relation":
                            rel = body["relation"]; rel["type"] = "dual_property" if "dual_property" in rel else "single_property"
                        api(f"v1/data_sources/{ds_of[d['name']]}", {"properties": {n: body}}, "PATCH"); print(kind, d["name"], n)
        # 4. formulas
        for d in spec:
            for n, expr in d["formulas"].items():
                api(f"v1/data_sources/{ds_of[d['name']]}", {"properties": {n: {"formula": {"expression": expr}}}}, "PATCH"); print("formula", d["name"], n)
        # 5. optional seed rows (only fully resolved ones)
        if a.seed:
            for d in spec:
                for row in d["seed_rows"]:
                    s = json.dumps(row)
                    for k, v in subs.items(): s = s.replace("{{" + k + "}}", v)
                    if "{{" in s: report.append(f"skipped seed row with unresolved placeholders in {d['name']}"); continue
                    api("v1/pages", {"parent": {"type": "data_source_id", "data_source_id": ds_of[d["name"]]}, "properties": to_api(d["properties"], json.loads(s))}); print("seed row", d["name"])
    # 6. page
    if page_md:
        for k, v in subs.items(): page_md = page_md.replace("{{" + k + "}}", v)
        try: r = api("v1/pages", {"parent": parent, "markdown": page_md, "markdown_version": "v2"})
        except RuntimeError as e: sys.exit(f"{e}\nThe page may exist anyway: search the parent for it before retrying; databases so far are in {a.manifest}")
        PID = r["id"]; track("page", PID); print("page", r.get("url", PID))
        # 7. linked views at their markers
        markers = re.findall(r"^\{\{VIEW:([^}]+)\}\}\s*$", page_md, re.M)
        for mk in markers:
            want_db, _, vname = mk.rpartition("/")
            cands = [(d, v) for d in spec for v in d["views"] if v["name"] == vname and (not want_db or d["name"] == want_db)]
            if not cands: report.append(f"no view spec for marker {mk}"); continue
            d, v = cands[0]
            if len(cands) > 1: report.append(f"ambiguous marker '{mk}', used database {d['name']} (use {{{{VIEW:Database/{vname}}}}})")
            ds = ds_of[d["name"]]; pids = {n: p["id"] for n, p in api(f"v1/data_sources/{ds}")["properties"].items()}
            if DRY: pids = {n: "DRY-" + n for n in d["properties"]}
            body = {"create_database": {"parent": parent | {"page_id": PID}, "show_data_source_title": False}, "data_source_id": ds, "name": v["name"], "type": v["type"]}
            if v.get("filter"): body["filter"] = v["filter"]
            if v.get("sorts"): body["sorts"] = v["sorts"]
            if v["type"] == "board":
                gp = v.get("group_by_property") or "Status"
                if gp not in pids: report.append(f"board {mk}: group property '{gp}' missing; skipped"); continue
                gt = next((t for t in d["properties"].get(gp, {"select": 0}) if t in ("select", "status", "multi_select")), "select")
                body["configuration"] = {"type": "board", "group_by": {"type": gt, "property_id": pids[gp], "sort": {"type": "manual"}}}
            elif v["type"] == "calendar":
                dp = v.get("date_property") or next((n for n, p in d["properties"].items() if "date" in p), None)
                if dp not in pids: report.append(f"calendar {mk}: no date property; skipped"); continue
                body["configuration"] = {"type": "calendar", "date_property_id": pids[dp]}
            elif v["type"] not in ("table", "list", "gallery"):
                report.append(f"view type '{v['type']}' for {mk} not tested; skipped"); continue
            api("v1/views", body)
            md = api(f"v1/pages/{PID}/markdown", query=["markdown_version==v2"])["markdown"]
            tags = re.findall(r"<database [^>]*></database>", md)
            if DRY or not tags: continue
            tag = tags[-1]
            m2 = re.search(r"\\?\{\\?\{VIEW:" + "".join(r"\\?" + re.escape(c) for c in mk) + r"\\?\}\\?\}", md)
            if not m2: report.append(f"marker text for {mk} not found in readback"); continue
            api(f"v1/pages/{PID}/markdown", {"markdown_version": "v2", "type": "update_content", "update_content": {"content_updates": [
                {"old_str": "\n\n" + tag, "new_str": ""}, {"old_str": m2.group(0), "new_str": tag}]}}, "PATCH")
            print("linked view placed:", mk)
        if not DRY:
            md = api(f"v1/pages/{PID}/markdown", query=["markdown_version==v2"])["markdown"]
            left = re.findall(r"VIEW:[^}\\]+", md)
            n_db = len(re.findall(r"<database ", md))
            print(f"verify: {n_db} linked databases on page, {len(left)} unresolved VIEW markers")
            if left: report.append(f"unresolved markers: {left}")
        un = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", md if not DRY else page_md)))
        if un: report.append(f"unfilled placeholders (pass --set KEY=VALUE): {un}")
    if not DRY: json.dump({"parent": a.parent, "template": tdir, "created": created}, open(a.manifest, "w"), indent=1)
    print("manifest:", a.manifest if not DRY else "(dry run: none written)"); [print("NOTE:", x) for x in report]

if __name__ == "__main__":
    main()
