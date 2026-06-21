"""CLI:
  python -m evidencepack --demo
  python -m evidencepack seal --tool unitgate --input "E = m * a" --status DIMENSIONALLY_INVALID
  python -m evidencepack verify pack.json
  python -m evidencepack diff a.json b.json
"""
import argparse
import json
import sys

from .pack import EvidencePack, verify, diff


def _demo():
    p = EvidencePack(tool_name="unitgate", tool_version="0.1.0",
                     raw_input="E = m * a", status="DIMENSIONALLY_INVALID",
                     result_body={"lhs_dimension": "M*L^2*T^-2", "rhs_dimension": "M*L*T^-2"},
                     replay_command="python -m unitgate --json \"E = m * a\"",
                     limitations=["dimensional consistency only"],
                     next_required_validation="none — dimensionally refuted").seal()
    print("# sealed pack"); print(json.dumps(p.to_dict(), indent=2))
    print("\n# verify"); print(json.dumps(verify(p.to_dict()), indent=2))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="evidencepack",
                                 description="Reproducible receipts for claim checks.")
    ap.add_argument("--demo", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("seal"); s.add_argument("--tool", required=True)
    s.add_argument("--input", required=True); s.add_argument("--status", required=True)
    s.add_argument("--version", default="0"); s.add_argument("--replay-command", default="")
    v = sub.add_parser("verify"); v.add_argument("pack")
    d = sub.add_parser("diff"); d.add_argument("a"); d.add_argument("b")
    args = ap.parse_args(argv)

    if args.demo or args.cmd is None and len(sys.argv) == 1:
        return _demo()
    if args.cmd == "seal":
        p = EvidencePack(tool_name=args.tool, tool_version=args.version,
                         raw_input=args.input, status=args.status,
                         replay_command=args.replay_command).seal()
        print(json.dumps(p.to_dict(), indent=2)); return 0
    if args.cmd == "verify":
        res = verify(json.load(open(args.pack, encoding="utf-8")))
        print(json.dumps(res, indent=2)); return 0 if res["status"] == "SEALED_OK" else 1
    if args.cmd == "diff":
        res = diff(json.load(open(args.a, encoding="utf-8")), json.load(open(args.b, encoding="utf-8")))
        print(json.dumps(res, indent=2)); return 0 if res["status"] == "MATCH" else 1
    if args.demo:
        return _demo()
    ap.print_help(); return 2


if __name__ == "__main__":
    sys.exit(main())
