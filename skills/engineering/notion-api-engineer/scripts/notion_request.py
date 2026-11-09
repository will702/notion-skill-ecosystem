#!/usr/bin/env python3
"""Stdlib-only wrapper around `ntn api` with retries and pagination.

Retry rules (see references/api-limits.md):
  * 429 / 529: always retried. `ntn` does not expose Retry-After on stdout,
    so we use exponential backoff with full jitter.
  * 500/502/503/504: retried only for GET and DELETE. POST/PATCH raise
    NtnError(retryable_after_verify=True): re-read the target and compare
    before retrying, otherwise a write that succeeded gets duplicated.
stdin is always closed (DEVNULL) so `ntn` cannot hang waiting for input.
No network code here; all traffic goes through the `ntn` binary.
"""
import argparse
import json
import random
import re
import subprocess
import sys
import time

IDEMPOTENT = {"GET", "DELETE"}
ALWAYS_RETRY = {429, 529}
SERVER_ERRORS = {500, 502, 503, 504}


class NtnError(Exception):
    def __init__(self, status, message, body=None, retryable_after_verify=False):
        super().__init__("HTTP %s: %s" % (status, message))
        self.status = status
        self.body = body
        self.retryable_after_verify = retryable_after_verify


def build_cmd(path, method=None, body=None, query=None, notion_version=None):
    cmd = ["ntn", "api", path]
    if method:
        cmd += ["-X", method.upper()]
    for key, value in (query or {}).items():
        cmd.append("%s==%s" % (key, value))
    if body is not None:
        cmd += ["-d", json.dumps(body)]
    if notion_version:
        cmd += ["--notion-version", notion_version]
    return cmd


def _parse(text):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _status_of(proc):
    """Best effort: HTTP status from the JSON error body, else from text."""
    for text in (proc.stdout, proc.stderr):
        data = _parse(text)
        if isinstance(data, dict) and isinstance(data.get("status"), int):
            return data["status"], data
    blob = (proc.stderr or "") + (proc.stdout or "")
    found = re.search(r"\b(4\d\d|5\d\d)\b", blob)
    return (int(found.group(1)) if found else 1), _parse(proc.stdout)


def effective_method(method, body):
    return (method or ("POST" if body is not None else "GET")).upper()


def request(path, method=None, body=None, query=None, notion_version=None,
            max_retries=5, base_delay=1.0, max_delay=60.0, timeout=120,
            dry_run=False):
    cmd = build_cmd(path, method, body, query, notion_version)
    if dry_run:
        print("DRY RUN:", " ".join(cmd), file=sys.stderr)
        return {}
    verb = effective_method(method, body)
    attempt = 0
    while True:
        proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=timeout)
        if proc.returncode == 0:
            return _parse(proc.stdout) if proc.stdout.strip() else {}
        status, data = _status_of(proc)
        message = (data or {}).get("message") if isinstance(data, dict) else None
        message = message or (proc.stderr or proc.stdout or "").strip()[:300]
        if isinstance(data, dict) and data.get("rate_limit_reason") == "public_api_request_blocked":
            raise NtnError(status, message, data)  # never retry this 429
        retry = status in ALWAYS_RETRY or (status in SERVER_ERRORS and verb in IDEMPOTENT)
        if status in SERVER_ERRORS and verb not in IDEMPOTENT:
            raise NtnError(status, message, data, retryable_after_verify=True)
        if not retry or attempt >= max_retries:
            raise NtnError(status, message, data)
        delay = random.uniform(0, min(max_delay, base_delay * (2 ** attempt)))
        print("retry %d/%d in %.1fs after HTTP %s" % (attempt + 1, max_retries, delay, status),
              file=sys.stderr)
        time.sleep(delay)
        attempt += 1


def paginate(path, body=None, method=None, page_size=100, notion_version=None,
             results_key="results", **kwargs):
    """Yield every item while has_more is true. POST endpoints (search,
    data_sources/<id>/query) carry start_cursor in the body; GET endpoints
    (blocks/<id>/children, users) carry it as a query param."""
    verb = effective_method(method, body)
    cursor = None
    while True:
        if verb == "GET":
            query = {"page_size": page_size}
            if cursor:
                query["start_cursor"] = cursor
            page = request(path, method, None, query, notion_version, **kwargs)
        else:
            payload = dict(body or {})
            payload["page_size"] = page_size
            if cursor:
                payload["start_cursor"] = cursor
            page = request(path, method or "POST", payload, None, notion_version, **kwargs)
        for item in page.get(results_key, []):
            yield item
        if not page.get("has_more"):
            return
        cursor = page.get("next_cursor")
        if not cursor:
            return


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Call `ntn api` with stdin closed, retries and optional pagination.")
    parser.add_argument("path", help="endpoint, for example v1/users/me")
    parser.add_argument("-X", "--method", help="HTTP method (default: GET, POST with --data)")
    parser.add_argument("-d", "--data", help="JSON request body")
    parser.add_argument("--paginate", action="store_true", help="follow has_more/next_cursor")
    parser.add_argument("--notion-version", help="pin Notion-Version for this call")
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true", help="print the command, do not run")
    args = parser.parse_args(argv)
    body = json.loads(args.data) if args.data else None
    opts = dict(max_retries=args.max_retries, dry_run=args.dry_run)
    try:
        if args.paginate:
            if args.dry_run:
                request(args.path, args.method, body, None, args.notion_version, dry_run=True)
                return 0
            print(json.dumps(list(paginate(args.path, body, args.method,
                                           notion_version=args.notion_version, **opts)), indent=2))
        else:
            print(json.dumps(request(args.path, args.method, body, None,
                                     args.notion_version, **opts), indent=2))
    except NtnError as err:
        print(str(err), file=sys.stderr)
        if err.retryable_after_verify:
            print("Write may have succeeded: re-read and compare before retrying.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
