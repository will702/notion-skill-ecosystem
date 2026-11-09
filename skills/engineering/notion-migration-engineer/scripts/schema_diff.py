#!/usr/bin/env python3
"""Diff two Notion data-source JSON files (output of GET v1/data_sources/<id>).

Compares property names, types and select/multi_select/status option names.
Usage: schema_diff.py OLD.json NEW.json
Exit code: 0 identical, 1 differences, 2 usage/read error.
Stdlib only, no network.
"""
import json
import sys

OPTION_TYPES = ("select", "multi_select", "status")


def load(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("properties", data)


def options(prop):
    kind = prop.get("type")
    if kind in OPTION_TYPES:
        return sorted(o.get("name", "") for o in prop.get(kind, {}).get("options", []))
    return []


def diff(old, new):
    lines = []
    for name in sorted(set(old) - set(new)):
        lines.append("MISSING in new: %s (%s)" % (name, old[name].get("type")))
    for name in sorted(set(new) - set(old)):
        lines.append("EXTRA in new:   %s (%s)" % (name, new[name].get("type")))
    for name in sorted(set(old) & set(new)):
        o, n = old[name], new[name]
        if o.get("type") != n.get("type"):
            lines.append("TYPE changed:  %s: %s -> %s" % (name, o.get("type"), n.get("type")))
            continue
        oo, no = options(o), options(n)
        if oo != no:
            lines.append("OPTIONS differ: %s (%s)" % (name, o.get("type")))
            for opt in sorted(set(oo) - set(no)):
                lines.append("    missing option: %s" % opt)
            for opt in sorted(set(no) - set(oo)):
                lines.append("    extra option:   %s" % opt)
    return lines


def main(argv):
    if len(argv) != 3 or argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 2
    try:
        old, new = load(argv[1]), load(argv[2])
    except (OSError, ValueError) as err:
        print("cannot read input: %s" % err, file=sys.stderr)
        return 2
    lines = diff(old, new)
    print("Schema diff: %s (%d properties) vs %s (%d properties)"
          % (argv[1], len(old), argv[2], len(new)))
    if not lines:
        print("OK: property names, types and select options match.")
        return 0
    print("\n".join(lines))
    print("%d difference(s)." % len(lines))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
