#!/usr/bin/env python
"""Turn an affiliate network on or off across the buying guides.

Flips site-config.json, rebuilds every guide, and optionally publishes. The
links are emitted or omitted at build time, so when a network is off it is
genuinely absent from the HTML rather than hidden with CSS.

    python tools/site_toggle.py status
    python tools/site_toggle.py aliexpress off
    python tools/site_toggle.py aliexpress on --deploy

Exit code is 0 on success, 1 on failure, so a caller can report honestly.
"""
import argparse, json, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "site-config.json"
NETWORKS = ("amazon", "aliexpress")

# Windows consoles default to cp1252 and cannot print the arrow or the Hebrew in
# the status output, which would crash the run mid-rebuild.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def read():
    return json.loads(CFG.read_text(encoding="utf-8"))


def status_line(cfg):
    a = cfg.get("affiliates", {})
    bits = [f"{n}={'ON' if a.get(n) else 'off'}" for n in NETWORKS]
    return " · ".join(bits) + f"  (changed {cfg.get('last_changed', '?')})"


def run(cmd, label):
    print(f"→ {label}")
    r = subprocess.run(cmd, cwd=ROOT, shell=isinstance(cmd, str),
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  FAILED: {(r.stderr or r.stdout).strip()[:400]}")
        return False
    tail = [l for l in (r.stdout or "").strip().splitlines() if l.strip()][-1:]
    if tail:
        print(f"  {tail[0][:160]}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("network", choices=list(NETWORKS) + ["status"])
    ap.add_argument("state", nargs="?", choices=["on", "off"])
    ap.add_argument("--deploy", action="store_true",
                    help="also publish to the live host")
    args = ap.parse_args()

    cfg = read()

    if args.network == "status":
        print(status_line(cfg))
        return 0
    if not args.state:
        sys.exit("need on or off")

    want = args.state == "on"
    cur = bool(cfg.setdefault("affiliates", {}).get(args.network, True))
    if cur == want:
        print(f"{args.network} already {'on' if want else 'off'} — nothing to do")
        print(status_line(cfg))
        return 0

    if not want and not any(v for k, v in cfg["affiliates"].items()
                            if k != args.network):
        sys.exit(f"refusing: turning {args.network} off would leave the guides "
                 f"with no buy links at all")

    cfg["affiliates"][args.network] = want
    cfg["last_changed"] = date.today().isoformat()
    CFG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    print(f"{args.network} -> {'ON' if want else 'off'}")

    if not run([sys.executable, "tools/build.py"], "rebuilding guides"):
        return 1

    if args.deploy:
        if not run(["bash", "deploy.sh"], "publishing to the live host"):
            return 1

    print(status_line(read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
