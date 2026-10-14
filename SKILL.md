---
name: reference-artifact
description: Build and iteratively refine a persistent two-column HTML reference document — main text on the left, aligned sidenotes on the right — that stays open in the side panel while the conversation continues in chat. Use this whenever the user asks for a reference document, explainer, primer, briefing, or study document they intend to keep and revise across several turns; whenever they mention sidenotes, marginal notes, footnotes in a side column, or a two-column reading layout; whenever they ask to add, revise, replace, or renumber content in a document already built this way; and whenever a question is a learning-oriented deep dive the user clearly wants to return to rather than read once and discard. Also use when the user says they want to "keep" or "build on" an answer instead of just receiving it.
---

# Reference artifact

Produce one self-contained HTML file: main column left (60%), sidenote column right (40%), notes vertically aligned with the paragraph that cites them. It lives in the side panel and gets revised turn by turn while the conversation happens in chat.

The document is a durable reference the user will return to months later, when they no longer remember which claims were checked. Everything below follows from that.

## Before the first draft

Ask one short question, offer a default, and don't block on the answer:

> Who's this for, and what job does it do — your own reference six months out, something to share, or a briefing before a meeting?

Then **write the answer into the document header**, as a visible line. A wrong guess must be visible on sight rather than silently shaping fifty small decisions about register, term-defining, and depth. If the user doesn't answer, record the assumption anyway:

```html
<p class="provenance-line">Written for: <em>the author, as personal reference</em> · assumed, not confirmed</p>
```

Also read the user's brief for format instructions and follow them exactly. They usually know what they want the page to look like; the template is a starting point, not a constraint on them.

## Four standing rules

These do not need to be re-requested each turn. They are always in force.

### 1. Verify before asserting, not after

Anything checkable gets checked **before it enters the document**, not defended afterward. That means:

- Any claim about what a named source says, or where in it something appears
- Any attribution of a term, phrase, or position to a person
- Any date, count, duration, or figure
- Any URL, paper, package, or book existing at all

Search, fetch, or grep the actual source. The characteristic failure is attributing plausible vocabulary to a source that never used it — the claim sits in the right neighbourhood, so it feels retrieved when it was generated. If a source can't be checked, it goes in as `UNVERIFIED` (below) or stays out.

### 2. Mark provenance on every note

The user's scarcest resource is verification effort. Direct it. Every sidenote carries one tag:

| Tag | Meaning |
|---|---|
| `VERIFIED` | Checked against a source retrieved this session. Pair with a citation block. |
| `UNVERIFIED` | Recalled, plausible, not checked. Genuinely might be wrong. |
| `MY READING` | Synthesis, framing, or inference. Not a fact claim at all. |

Never leave a note untagged — absence of a tag is indistinguishable from a forgotten tag, which defeats the purpose.

### 3. Propose, then let the user pick

When the user says a passage is unclear, wrong, or not landing, **do not silently rewrite it.** Offer 3–4 labelled alternatives in chat, each taking a genuinely different approach — not four rewordings of one idea. Say which you'd choose and why. Apply only the one they name.

Before writing options, diagnose. "Unclear" usually means one of:

- **A term wasn't defined** → a footnote fixes it
- **A term was imported from outside the source** → check the source; the word may be wrong, not just unexplained
- **The mental model is wrong** → no rewording will work; the options must attack the model

If the user states what they *think* a passage means, that is the diagnosis — use it. If two rounds of options both fail, stop rewording and ask what they understood it to say.

### 4. Declare additions the user didn't ask for

Adding a relevant fact, a counter-argument, or a connection is usually good. Doing it invisibly is not. Make the addition, then name it in chat in one line, so the user can cut it. Include the strongest opposing source when one exists — a reference document that hides its best counter-argument is less useful, not more.

## Document structure

Copy `assets/template.html` and fill it in. It already contains the layout, type scale, palette, provenance tags, and the numbering script. Sections in order:

1. **Masthead** — title, one-line standfirst, the "Written for" line
2. **The question** — the user's original brief, verbatim, in italics
3. **Numbered sections** (`01 /`, `02 /` …) — numbers exist so the user can say "add a footnote in section 3" and be unambiguous
4. **Open questions** — always last, before the footer

The open-questions block holds anything unresolved: choices the user hasn't made, offers not taken up, claims still unverified. Questions asked in chat evaporate; questions in the document persist. It also carries this standing line, which belongs in front of the user at the moment of confusion rather than buried in this file:

> When something doesn't land, say what you think it means. A wrong guess diagnoses faster than "unclear."

### Sections and rows

Each paragraph (or small group) is one `.row` — main content in column one, its notes in column two. That per-row grid is what aligns a note with the text citing it. One row per paragraph gives tight alignment; batching paragraphs loosens it.

Two rules follow from that grid, and both are load-bearing:

- **A mark attaches to the words its note is about** — not to the end of whichever sentence is nearby. If the note explains a term, the mark goes on the term.
- **A note lives in the same `.row` as its mark**, in the same order as the marks in that row. Alignment is per-row, so a note filed one row early renders beside the wrong paragraph while every slug still resolves correctly.

If a note has no sentence it can honestly attach to, the document is missing a sentence. Write it, or cut the note. Do not park the note on the nearest available anchor.

## Never store a number you can derive

Footnote numbers are **computed at render time from document order.** Reference marks carry a slug, not an integer:

```html
<a class="ref" data-note="closed-form"></a>
...
<div class="note" data-note="closed-form"><span class="n"></span>
  <span class="tag t-verified">verified</span> <b>Closed form</b>: …
</div>
```

The inline script in the template walks refs in document order, assigns 1..n, and writes the number into both the mark and the note. Inserting a note in the middle is a pure insert with no renumbering, and a note nothing points at renders with `!` and a red rule so orphans are visible rather than silent.

This matters because manual renumbering is where this workflow breaks. Every insert touches every downstream number, and a single off-by-one produces duplicate footnotes that are easy to miss and hard to spot later.

## After every edit

Run the structural checker:

```bash
python3 scripts/check.py path/to/document.html
```

It verifies that refs and notes correspond one-to-one, that every note carries a provenance tag, that no note is orphaned, and that **each note sits in the same `.row` as the mark pointing at it, in the same order as the marks in that row**.

That last check exists because the others are slug-level and the layout is row-level. A note filed in the wrong row resolves fine, numbers fine, and renders beside the wrong paragraph. Nothing else catches it.

Fix what it reports before presenting.

## Before presenting a new or rewritten section

Structure being right does not make a note relevant. Run:

```bash
python3 scripts/review.py path/to/document.html
```

For each mark it prints the anchor — the paragraph the mark sits in — next to the opening of its note. It always exits 0. It decides nothing. Its only job is to put the two halves of each footnote on adjacent lines so they get compared in one view instead of across a scroll.

**Read the output and give every note a verdict before presenting.** Three outcomes:

- the note explains or supports the marked words → leave it
- the note is about something the document says elsewhere → move the mark to that sentence
- the note is about something the document never says → write the sentence, or cut the note

The failure this catches is a note that is interesting, correct, well-sourced, and attached to the nearest convenient sentence rather than to its subject. It passes every structural check. The reader hits a mark on one topic and reads a note on another, and reasonably concludes the numbering is broken.

Skipping this step is easy precisely because the script never fails. The verdict is the step; the script is only what makes the verdict cheap.

Then present the file so the panel refreshes — the user asked for it to stay visible, and it only stays current if re-presented.

## The revision loop

1. User names a target — a section, a footnote number, a quoted phrase
2. Diagnose before drafting; check any source the change touches
3. Small factual addition → make it. Contested wording → propose options and stop
4. Apply, run `check.py`, and in **one or two lines** say what changed and flag anything you added beyond the request. Run `review.py` as well whenever the edit added a note, moved a mark, or rewrote a paragraph that carries one — those are exactly the edits that strand a note on the wrong anchor

Keep chat replies short. The document carries the content; chat carries the decisions. Don't restate in prose what the reader can see in the panel.

## Periodically, unprompted

Offer these when the document has grown past roughly ten sections or twenty notes:

- **An adversarial pass** — "the five claims here most likely to be wrong, ranked." Volunteering weak spots is unreliable; producing them on demand is not, so make the demand.
- **A scope check** — these documents grow without anything stopping them. Say so once.
- **A pass converting summaries into pointers** — for a learning document, a footnote that points at a primary source is worth more than a footnote that paraphrases it. The document is better as an index into verified material than as a container of claims.
