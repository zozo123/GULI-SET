"""Verify or regenerate the repository's tracked-file SHA-256 manifest.

Usage:
    python scripts/verify_manifest.py
    python scripts/verify_manifest.py --write

The manifest deliberately excludes itself.  Its file set comes from ``git ls-files``
rather than a hand-maintained glob, so a newly tracked release artifact cannot escape
verification merely because nobody remembered to add its path to this script.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"


def tracked_files() -> tuple[Path, ...]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(raw.decode("utf-8"))
        if relative == MANIFEST.relative_to(ROOT):
            continue
        path = ROOT / relative
        if path.is_symlink():
            raise ValueError(f"tracked symlinks are not supported: {relative.as_posix()}")
        if not path.is_file():
            raise ValueError(f"tracked path is not a regular file: {relative.as_posix()}")
        paths.append(relative)
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def render_manifest() -> str:
    lines = []
    for relative in tracked_files():
        digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        lines.append(f"{digest}  {relative.as_posix()}")
    return "\n".join(lines) + "\n"


def verify_manifest() -> None:
    expected = render_manifest()
    try:
        actual = MANIFEST.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValueError(f"missing manifest: {MANIFEST.relative_to(ROOT)}") from exc
    if actual != expected:
        diff = "".join(
            difflib.unified_diff(
                actual.splitlines(keepends=True),
                expected.splitlines(keepends=True),
                fromfile="committed/MANIFEST.sha256",
                tofile="expected/MANIFEST.sha256",
            )
        )
        raise ValueError(
            "MANIFEST.sha256 is stale or incomplete; run "
            "`python scripts/verify_manifest.py --write` after staging tracked files.\n"
            + diff
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="replace the manifest")
    args = parser.parse_args()
    if args.write:
        MANIFEST.write_text(render_manifest(), encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(ROOT)}")
    else:
        verify_manifest()
        print(f"verified {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
