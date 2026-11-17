#!/usr/bin/env python3
"""Build themes/outback.json from palette.toml and src/outback.json.

In src/outback.json a colour is written by its palette name: "$ochre" becomes
"#ee7a3c", and "$ochre/59" becomes "#ee7a3c59" (the suffix is a hex alpha).

Usage:
    python3 -I build.py           # rewrite themes/outback.json
    python3 -I build.py --check   # exit 1 if it is out of date
"""

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PALETTE = ROOT / "palette.toml"
SRC = ROOT / "src/outback.json"
OUT = ROOT / "themes/outback.json"

REF = re.compile(r'"\$([a-z][a-z-]*)(?:/([0-9a-f]{2}))?"')
NAME_LINE = '  "name": "Outback",\n'
NOTE = ('  "$comment": "Generated from palette.toml and src/outback.json by build.py. '
        "Don't edit by hand; run make theme.\",\n")


def die(msg):
    sys.exit(f"build.py: {msg}")


def load_palette():
    colours = tomllib.loads(PALETTE.read_text())["colours"]
    for name, c in colours.items():
        if not re.fullmatch(r"#[0-9a-f]{6}", c):
            die(f"{PALETTE.name}: '{name}' must be a lowercase #rrggbb colour, not '{c}'")
    return colours


def build():
    colours = load_palette()
    src = SRC.read_text()
    used, unknown = set(), set()

    def sub(m):
        name, alpha = m.groups()
        if name not in colours:
            unknown.add(name)
            return m.group(0)
        used.add(name)
        return f'"{colours[name]}{alpha or ""}"'

    out = REF.sub(sub, src)
    if unknown:
        die(f"{SRC.relative_to(ROOT)} uses names not in {PALETTE.name}: {', '.join(sorted(unknown))}")
    if unused := set(colours) - used:
        die(f"{PALETTE.name} has colours the theme never uses: {', '.join(sorted(unused))}")
    if (stray := re.findall(r'"#[0-9a-fA-F]{3,8}"', src)):
        die(f"{SRC.relative_to(ROOT)} has raw hex colours; use palette names: {', '.join(sorted(set(stray)))}")
    if out.count(NAME_LINE) != 1:
        die(f"expected one line {NAME_LINE.strip()!r} in {SRC.relative_to(ROOT)}")
    out = out.replace(NAME_LINE, NAME_LINE + NOTE)
    json.loads(out)  # fail here, not in the editor, if the result isn't valid JSON
    return out


def main():
    check = "--check" in sys.argv[1:]
    text = build()
    current = OUT.read_text() if OUT.exists() else None
    if current == text:
        print(f"{OUT.relative_to(ROOT)} is up to date")
    elif check:
        print(f"out of date: {OUT.relative_to(ROOT)} (run make theme)")
        sys.exit(1)
    else:
        OUT.write_text(text)
        print(f"updated: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
