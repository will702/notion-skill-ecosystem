#!/usr/bin/env python3
"""Create a row in a Notion data source only if no row has the same Dedupe Key.

Usage:
  create_if_absent.py <DATA_SOURCE_ID> "<Name>" "<Dedupe Key>" [YYYY-MM-DD]

Example key for a weekly task: "weekly-review-2026-W46".
Requires `ntn` on PATH and a data source with properties:
  Name (title), Dedupe Key (rich_text), Due Date (date, optional).
Exit codes: 0 created or already present, 1 error (verify by hand if unsure).
"""
import json
import subprocess
import sys
import time


def ntn(args, body=None):
    cmd = ["ntn", "api"] + args
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    # stdin closed so ntn never hangs in cron/launchd
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def query_by_key(ds_id, key):
    body = {
        "filter": {"property": "Dedupe Key", "rich_text": {"equals": key}},
        "page_size": 5,
    }
    for attempt in range(4):  # query is a read: safe to retry
        code, out, err = ntn(["v1/data_sources/%s/query" % ds_id, "-X", "POST"], body)
        if code == 0:
            try:
                return json.loads(out).get("results", [])
            except ValueError:
                pass
        time.sleep(min(2 ** attempt, 8))  # about 3 req/s limit: back off
    raise RuntimeError("query failed: " + err.strip()[:300])


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 1
    ds_id, name, key = argv[1], argv[2], argv[3]
    due = argv[4] if len(argv) > 4 else None
    if query_by_key(ds_id, key):
        print("exists: %s (skipped)" % key)
        return 0
    props = {
        "Name": {"title": [{"text": {"content": name[:2000]}}]},
        "Dedupe Key": {"rich_text": [{"text": {"content": key[:2000]}}]},
    }
    if due:
        props["Due Date"] = {"date": {"start": due}}
    body = {"parent": {"type": "data_source_id", "data_source_id": ds_id}, "properties": props}
    # Single attempt: never blind-retry a POST.
    code, out, err = ntn(["v1/pages", "-X", "POST"], body)
    if code == 0:
        print("created: %s" % key)
        return 0
    # Failure: the write may still have landed. Re-read before reporting.
    if query_by_key(ds_id, key):
        print("created despite error: %s" % key)
        return 0
    print("not created: " + err.strip()[:300], file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
