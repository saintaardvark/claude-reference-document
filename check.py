#!/usr/bin/env python3
"""Structural checks for a reference-artifact document.

Run after every edit, before presenting the file:

    python3 scripts/check.py document.html

Checks:
  1. Every reference mark points at a note that exists.
  2. Every note is pointed at by at least one reference mark.
  3. Reference marks and notes use data-note slugs, not hardcoded numbers.
  4. Every substantive note carries exactly one provenance tag.
  5. Slugs are unique per note (no two notes claiming the same slug).
  6. The audience line is filled in, and no template placeholders survive.
  7. Every note sits in the same .row as the mark that points at it.
  8. Within a row, notes appear in the same order as their marks.

Checks 7 and 8 exist because 1-6 are slug-level and the layout is row-level:
a note filed in the wrong row resolves fine, numbers fine, and renders beside
the wrong paragraph. Nothing else catches that.

What this cannot check is whether a note is *about* the text it is attached
to. Use review.py for that; it needs a reader, not a script.

Exit code 0 if clean, 1 if anything failed.
"""

import re
import sys
from collections import Counter

import docmodel as dm

TAGS = ("t-verified", "t-unverified", "t-mine")


def tag_classes(note):
    """Provenance tag classes appearing anywhere inside a note."""
    found = set()
    for node in note.walk():
        found |= node.classes & set(TAGS)
    return found


def main(path):
    root = dm.parse(path)
    raw = open(path, encoding="utf-8").read()

    marks = dm.marks(root)
    notes = dm.notes(root)
    number = dm.numbering(root)

    ref_slugs = [m.get("data-note") for m in marks]
    note_slugs = [n.get("data-note") for n in notes]
    ref_set, note_set = set(ref_slugs), set(note_slugs)

    problems, warnings = [], []

    def label(slug):
        n = number.get(slug)
        return f"[{n}] {slug!r}" if n else f"{slug!r}"

    # 1 & 2 — correspondence
    for slug in sorted(ref_set - note_set):
        problems.append(f"reference mark points at a missing note: {slug!r}")
    for slug in sorted(note_set - ref_set):
        problems.append(f"note is orphaned, nothing references it: {slug!r}")

    # 3 — no hardcoded numbering left behind
    if re.search(r'<a[^>]*class="ref"[^>]*href="#n\d+"', raw):
        problems.append("a reference mark uses a hardcoded #nN href; use data-note slugs")
    for note in notes:
        for span in note.walk():
            if "n" in span.classes and span.text().strip().isdigit():
                problems.append(
                    f"note {label(note.get('data-note'))} has a hardcoded number; "
                    'leave <span class="n"></span> empty'
                )

    # 4 — provenance
    for note in notes:
        found = tag_classes(note)
        if not found:
            problems.append(
                f"note {label(note.get('data-note'))} has no provenance tag "
                "(verified / unverified / my reading)"
            )
        elif len(found) > 1:
            problems.append(
                f"note {label(note.get('data-note'))} has multiple provenance tags: "
                + ", ".join(sorted(found))
            )

    # 5 — duplicate slugs
    for slug, count in Counter(note_slugs).items():
        if count > 1:
            problems.append(f"slug {slug!r} is used by {count} notes; slugs must be unique")

    # 6 — placeholders and audience
    leftover = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", raw)))
    if leftover:
        problems.append("unfilled template placeholders: " + ", ".join(leftover))
    if not any("provenance-line" in n.classes for n in root.walk()):
        problems.append("missing the 'Written for:' audience line in the masthead")

    # 7 — a note belongs in the row holding its mark
    row_index = {row: i for i, row in enumerate(dm.rows(root))}
    mark_row = {}
    for mark in marks:
        slug = mark.get("data-note")
        row = dm.row_of(mark)
        mark_row.setdefault(slug, row_index.get(row))

    for note in notes:
        slug = note.get("data-note")
        if slug not in mark_row:
            continue  # already reported as orphaned
        here = row_index.get(dm.row_of(note))
        there = mark_row[slug]
        if here != there:
            problems.append(
                f"note {label(slug)} is in row {here}, but its mark is in row {there}; "
                "it will render beside the wrong paragraph"
            )

    # 8 — within a row, note order must follow mark order
    for i, row in enumerate(dm.rows(root)):
        in_row_marks, seen = [], set()
        for mark in dm.marks(row):
            slug = mark.get("data-note")
            if slug not in seen:
                seen.add(slug)
                in_row_marks.append(slug)
        in_row_notes = [n.get("data-note") for n in dm.notes(row)]

        expected = [s for s in in_row_marks if s in in_row_notes]
        actual = [s for s in in_row_notes if s in in_row_marks]
        if expected != actual:
            problems.append(
                f"row {i}: notes are ordered "
                f"{[number.get(s) for s in actual]} but their marks run "
                f"{[number.get(s) for s in expected]}; reorder the notes column"
            )

    # Advisory, not fatal
    unverified = sum(1 for n in notes if "t-unverified" in tag_classes(n))
    if unverified:
        warnings.append(
            f"{unverified} note(s) tagged UNVERIFIED — check or remove before this is relied on"
        )
    if not any("open" in n.classes for n in root.walk()):
        warnings.append("no open-questions block found; it belongs at the end of the document")

    print(f"{len(marks)} reference marks, {len(notes)} notes, {len(ref_set)} distinct slugs")

    for w in warnings:
        print(f"  note: {w}")

    if problems:
        print(f"\nFAILED — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("\nOK — refs and notes correspond, all tagged, each note beside its mark.")
    print("Structure only. Run review.py to judge whether the notes are relevant.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
