#!/usr/bin/env python3
"""Minimal HTML tree for reference-artifact documents.

Both check.py and review.py need element *containment* — which row a note
sits in, which paragraph a mark sits in. Regexes can't answer that on nested
divs, so this builds a small tree with the standard library only.

No third-party dependencies. Not a general-purpose HTML parser; it assumes
the well-formed markup the template produces.
"""

from html.parser import HTMLParser

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img",
    "input", "link", "meta", "param", "source", "track", "wbr",
}

# Elements treated as the "anchor block" for a reference mark.
BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "td", "th", "blockquote"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children = []
        self.parent = parent

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())

    def get(self, name, default=None):
        return self.attrs.get(name, default)

    def text(self):
        """Visible text, whitespace-collapsed."""
        parts = []
        for child in self.children:
            parts.append(child if isinstance(child, str) else child.text())
        return " ".join("".join(parts).split())

    def walk(self):
        """Every descendant Node, in document order."""
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.walk()

    def ancestor(self, predicate):
        """Nearest ancestor satisfying predicate, or None."""
        node = self.parent
        while node is not None:
            if predicate(node):
                return node
            node = node.parent
        return None

    def __repr__(self):
        cls = self.get("class", "")
        return f"<{self.tag}{' class=' + cls if cls else ''}>"


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, dict(attrs), self.stack[-1]))

    def handle_endtag(self, tag):
        # Tolerate stray close tags: unwind to the matching open element only.
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse(path):
    with open(path, encoding="utf-8") as fh:
        builder = _Builder()
        builder.feed(fh.read())
        return builder.root


# ---------------------------------------------------------------- queries

def rows(root):
    """Alignment rows, in document order.

    Only elements carrying class 'row'. A '.open' section wraps its own
    '.row', so selecting 'row' alone avoids counting that block twice.
    """
    return [n for n in root.walk() if "row" in n.classes]


def marks(root):
    """Reference marks carrying a data-note slug, in document order."""
    return [
        n for n in root.walk()
        if n.tag == "a" and "ref" in n.classes and n.get("data-note")
    ]


def notes(root):
    """Sidenotes carrying a data-note slug, in document order.

    Citation blocks (class 'note cite', no data-note) are deliberately
    excluded — they are unnumbered companions to the note above them.
    """
    return [
        n for n in root.walk()
        if "note" in n.classes and n.get("data-note")
    ]


def row_of(node):
    """The .row containing this node, or None."""
    return node.ancestor(lambda n: "row" in n.classes)


def anchor_of(mark):
    """The block element a reference mark sits in.

    Falls back to the containing .main, then to the parent, so a mark
    placed somewhere unexpected still reports something readable rather
    than crashing.
    """
    block = mark.ancestor(lambda n: n.tag in BLOCK)
    if block is not None:
        return block
    return mark.ancestor(lambda n: "main" in n.classes) or mark.parent


def numbering(root):
    """slug -> footnote number, derived exactly as the document's JS does."""
    order = {}
    for mark in marks(root):
        slug = mark.get("data-note")
        if slug not in order:
            order[slug] = len(order) + 1
    return order
