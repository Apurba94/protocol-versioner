"""Command-line interface for protocol-versioner."""
import argparse
import sys

from .core import ProtocolStore


def _read(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="protocol-versioner", description="Version-controlled lab protocols.")
    ap.add_argument("--root", default="protocols")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("name")
    a.add_argument("file")
    a.add_argument("--author", default="")
    u = sub.add_parser("update")
    u.add_argument("name")
    u.add_argument("file")
    u.add_argument("-m", "--note", required=True)
    u.add_argument("--author", default="")
    sub.add_parser("list")
    h = sub.add_parser("history")
    h.add_argument("name")
    s = sub.add_parser("show")
    s.add_argument("name")
    s.add_argument("-v", "--version", type=int)
    d = sub.add_parser("diff")
    d.add_argument("name")
    d.add_argument("a", type=int)
    d.add_argument("b", type=int)
    r = sub.add_parser("retire")
    r.add_argument("name")
    r.add_argument("--reason", default="")
    args = ap.parse_args(argv)
    st = ProtocolStore(args.root)
    try:
        if args.cmd == "add":
            print("%s v%d" % (args.name, st.add(args.name, _read(args.file), args.author)))
        elif args.cmd == "update":
            print("%s v%d" % (args.name, st.update(args.name, _read(args.file), args.author, args.note)))
        elif args.cmd == "list":
            for p in st.protocols():
                print("%-30s v%-3d %s  %-8s %s" % (p["name"], p["versions"], p["updated"][:10], p["status"], p["title"]))
        elif args.cmd == "history":
            for v in st.history(args.name):
                print("v%03d  %s  %-15s %s" % (v["version"], v["date"][:16], v["author"] or "-", v["note"]))
        elif args.cmd == "show":
            sys.stdout.write(st.export(args.name, args.version))
        elif args.cmd == "diff":
            sys.stdout.write(st.diff(args.name, args.a, args.b) or "no differences\n")
        elif args.cmd == "retire":
            st.retire(args.name, args.reason)
    except (KeyError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    return 0
