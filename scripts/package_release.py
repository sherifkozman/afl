#!/usr/bin/env python3
"""Package the repo into a distributable zip (for GitHub releases).

Usage:
  python3 scripts/package_release.py --out dist/afl.zip
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/afl.zip")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    out_path = repo_root / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in repo_root.rglob("*"):
            if p.is_dir():
                continue
            rel = p.relative_to(repo_root)
            # skip dist artifacts
            if rel.parts and rel.parts[0] == "dist":
                continue
            z.write(p, arcname=str(rel))

    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
