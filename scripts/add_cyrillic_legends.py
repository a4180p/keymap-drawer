#!/usr/bin/env python3
"""Add Russian (ЙЦУКЕН) legends to the bottom-right corner of keys in a keymap YAML.

Maps by the Latin legend already shown on each key, which is correct when any
alternative layout is applied in firmware. Keys with no match are left untouched.

When a key gains a Cyrillic legend and also has a hold legend, the hold legend is
moved to the bottom-left corner so the two do not collide. Keys without a Cyrillic
legend keep their hold legend centered.
"""

import argparse
import contextlib
import sys

import yaml

# QWERTY position -> Russian character
CYRILLIC = {
    "Q": "й", "W": "ц", "E": "у", "R": "к", "T": "е",
    "Y": "н", "U": "г", "I": "ш", "O": "щ", "P": "з",
    "A": "ф", "S": "ы", "D": "в", "F": "а", "G": "п",
    "H": "р", "J": "о", "K": "л", "L": "д",
    "Z": "я", "X": "ч", "C": "с", "V": "м", "B": "и",
    "N": "т", "M": "ь",
    "[": "х", "]": "ъ", ";": "ж", "'": "э",
    ",": "б", ".": "ю", "/": ".", "`": "ё",
}

TAP_ALIASES = ("t", "tap", "center")
HOLD_ALIASES = ("h", "hold", "bottom")


def annotate_key(key):
    """Return key with a `br` legend added, if its tap legend maps to Cyrillic."""
    if isinstance(key, str):
        tap, out = key, {"t": key}
    elif isinstance(key, dict):
        field = next((f for f in TAP_ALIASES if f in key), None)
        if field is None:
            return key
        tap, out = key[field], dict(key)
    else:
        return key

    if not isinstance(tap, str):
        return key

    char = CYRILLIC.get(tap if tap in CYRILLIC else tap.upper())
    if char is None or "br" in out:
        return key

    out["br"] = char

    # move a centered hold legend out of the way, but only on keys that gained Cyrillic
    hold_field = next((f for f in HOLD_ALIASES if f in out), None)
    if hold_field is not None and "bl" not in out:
        out["bl"] = out.pop(hold_field)

    return out


def walk(node):
    if isinstance(node, list):
        return [walk(item) for item in node]
    return annotate_key(node)


def dump(data, path):
    """Write YAML to path, or stdout when path is None."""
    try:
        with open(path, "w", encoding="utf-8") if path else contextlib.nullcontext(sys.stdout) as out:
            yaml.safe_dump(data, out, width=160, sort_keys=False, default_flow_style=None, allow_unicode=True)
    except OSError as exc:
        raise SystemExit(f"cannot write output: {exc}") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keymap", help="path to keymap YAML")
    parser.add_argument("-o", "--output", help="output path (default: stdout)")
    args = parser.parse_args()

    try:
        with open(args.keymap, encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except OSError as exc:
        parser.error(f"cannot read {args.keymap}: {exc}")
    except yaml.YAMLError as exc:
        parser.error(f"invalid YAML in {args.keymap}: {exc}")

    if not isinstance(data, dict):
        parser.error(f"{args.keymap} does not contain a keymap mapping")

    for name, layer in data.get("layers", {}).items():
        data["layers"][name] = walk(layer)

    try:
        dump(data, args.output)
    except OSError as exc:  # pragma: no cover - dump already reports write errors
        parser.error(f"cannot write output: {exc}")


if __name__ == "__main__":
    main()
