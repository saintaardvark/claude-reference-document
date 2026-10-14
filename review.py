#!/usr/bin/env python3
"""Relevance review for a reference-artifact document.

    python3 scripts/review.py document.html
    python3 scripts/review.py document.html --slug userspace
    python3 scripts/review.py document.html --width 100

For each reference mark, prints the anchor — the paragraph the mark sits in,
with the mark's position shown as [^n] — beside the note it points at.

This script decides nothing and always exits 0. Its only job is to put the
two halves of each footnote on adjacent lines, so they get compared in one
view instead of across a scroll. check.py already proves the structure is
sound; a note can pass every one of those checks and still be about a
different subject than the words it hangs off.

Read the output and give every note a verdict:

  - the note explains or supports the marked words        -> leave it
  - the note is about something the document says elsewhere -> move the mark
  - the note is about something the document never says   -> write the
    sentence it needs, or cut the note

The characteristic failure is a note that is interesting, correct, and
well-sourced, attached to the nearest convenient sentence rather than to its
subject. The reader hits a mark on one topic, reads a note on another, and
concludes the numbering is broken.
"""

import argparse
import sys
import textwrap

import docmodel as dm

TAG_NAMES = {
    "t-verified": "VERIFIED",
    "t-unverified": "UNVERIFIED",
    "t-mine": "MY READING",
}


def provenance(note):
    for node in note.walk():
        for cls in node.classes:
            if cls in TAG_NAMES:
                return TAG_NAMES[cls]
    return "UNTAGGED"


def note_body(note):
    """Note text without its provenance tag or number span."""
    skip = set()
    for node in note.walk():
        if node.classes & (set(TAG_NAMES) | {"n"}):
            skip.add(id(node))

    parts = []

    def collect(node):
        for child in node.children:
            if isinstance(child, str):
                parts.append(child)
            elif id(child) not in skip:
                collect(child)

    collect(note)
    return " ".join("".join(parts).split())


def anchor_text(mark, number):
    """Anchor block text with the mark's own position made visible."""
    block = dm.anchor_of(mark)
    if block is None:
        return "(no containing block)"

    parts = []

    def collect(node):
        for child in node.children:
            if isinstance(child, str):
                parts.append(child)
            elif child is mark:
                parts.append(f" [^{number}] ")
            else:
                collect(child)

    collect(block)
    return " ".join("".join(parts).split())


def main(argv):
    ap = argparse.ArgumentParser(description="Pair each footnote with the text it is attached to.")
    ap.add_argument("path")
    ap.add_argument("--slug", help="review one note only")
    ap.add_argument("--width", type=int, default=88, help="wrap column (default 88)")
    args = ap.parse_args(argv)

    root = dm.parse(args.path)
    number = dm.numbering(root)
    notes = {n.get("data-note"): n for n in dm.notes(root)}

    def block(label, body, width):
        pad = " " * (len(label) + 1)
        wrapped = textwrap.wrap(body, width=width - len(pad)) or ["(empty)"]
        print(f"{label} {wrapped[0]}")
        for line in wrapped[1:]:
            print(f"{pad}{line}")

    shown = 0
    seen = set()
    for mark in dm.marks(root):
        slug = mark.get("data-note")
        if slug in seen:
            continue
        seen.add(slug)
        if args.slug and slug != args.slug:
            continue

        n = number[slug]
        note = notes.get(slug)

        print()
        print(f"[{n}] {slug}   {provenance(note) if note else '*** NO SUCH NOTE ***'}")
        block("  ANCHOR", anchor_text(mark, n), args.width)
        block("  NOTE  ", note_body(note) if note else "(missing)", args.width)
        shown += 1

    if not shown:
        print(f"\nNothing to review{' for slug ' + args.slug if args.slug else ''}.")
        return 0

    print()
    print("-" * args.width)
    print(f"{shown} note(s). This script decides nothing — give each one a verdict before presenting:")
    print("  keep it / move the mark to the sentence it belongs to / write the")
    print("  missing sentence or cut the note.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
