# Epic 7 — Terminal Rendering

PRD for Terminal Rendering. Requirements only — no technical or architectural decisions.

> **Confidence:** ~94% after Cycle 2 — all six Cycle 1 ambiguities are resolved and reconciled into §5–§10 as direct statements (reverse-video highlighting, search-dialog scrolling matching the match list, match/selection list drawn as a modal, redraw-on-resize, truncate-on-overflow, and a required Unicode box-drawing terminal with no ASCII fallback); §13 is empty and no open questions remain. The only residual softness is that journeys 6.1–6.6 don't separately narrate the resize/overflow edge cases — they're fully specified as FR14/FR15 and AC14/AC15 instead, which is an acceptable level of detail for edge-case behavior rather than a distinct user journey.

## 1. Summary

An operator actually sees dbbro's screens drawn in the terminal — the
search selection dialog, the search value prompt, the table view, the
match/selection list, and the error notice — using the panel and modal
box-drawing styles described in the briefing. Every screen and interaction
already exists as far as what the operator can *do* (select, type, submit,
navigate, dismiss); this epic is about what the operator *sees* while doing
it.

## 2. Goals

- Let an operator see the search selection dialog drawn as a modal box
  listing every table/column search pair, with the highlighted pair
  visually distinguished.
- Let an operator see the search value prompt drawn as a modal box showing
  the selected table/column label and the value typed so far.
- Let an operator see a matched record's table view drawn as a bordered
  panel, one row per configured column, with the selected field visually
  distinguished and relation values shown in the `<table>[<fk>]` format.
- Let an operator see a match/selection list (when a search or relation
  lookup finds more than one record) drawn with the highlighted candidate
  visually distinguished.
- Let an operator see the error notice drawn as a modal box that stays
  until dismissed.
- Ensure that whichever screen is currently active is the only one visibly
  drawn — no leftover or overlapping content from a screen that is no
  longer active.

## 3. Out of scope

- Any change to what the operator can *do* on a screen (key handling,
  selection logic, search/lookup/navigation behaviour) — that is already
  defined by EP-2 (Record Search), EP-3 (Entry Table View), EP-4 (Browsing
  History), and EP-5 (Error Reporting). This epic only draws what those
  epics already decide is on screen.
- Declaring or validating the schema or database connection (EP-1, EP-6).
- Color, theming, or any styling beyond distinguishing the highlighted
  item and drawing the panel/modal borders described in the briefing.
- Localization or translation of any on-screen text.

## 4. Personas

- **Operator** — the same persona as every other epic: uses dbbro's
  screens to search, view, and navigate records, and needs to actually see
  what they are selecting, typing, or being told.

## 5. Domain concepts

- **Panel** — a single-line-bordered box (using the briefing's panel
  character set: `┌─┬─┐`, `├─┼─┤`, `│`, `└─┴─┘`) used to draw a record's
  table view.
- **Modal** — a double-line-bordered box (using the briefing's modal
  character set: `╔═╦═╗`, `╠═╬═╣`, `║`, `╚═╩═╝`) used to draw the search
  selection dialog, the search value prompt, and the error notice.
- **Highlight** — the visual distinction applied to whichever item
  (search pair, table view field, or match-list row) is currently
  selected, so the operator can always tell where they are. Rendered as
  reverse video (swapped foreground/background colors) on that item's
  line.
- **Active screen** — whichever single screen (dialog, prompt, table view,
  match list, or error notice) is currently meant to be visible; drawing
  it must not leave visible remnants of whatever was drawn before it.
- **Match/selection list** — drawn as a modal (double-line border), the
  same visual family as the search selection dialog, since both are
  transient "pick one and confirm" popups.

## 6. User journeys

### 6.1 Operator sees the search selection dialog
On startup, or after pressing `s`, the operator sees a modal box listing
every table/column search pair the configuration declares, with the pair
the operator would select by pressing Return shown in reverse video. If
there are more pairs than fit within the modal, the list scrolls (the same
way the match/selection list already scrolls) to keep the highlighted pair
visible.

### 6.2 Operator sees the search value prompt
After selecting a pair, the operator sees a modal box showing that
table/column pair's label and the value they have typed so far, updating
as they type.

### 6.3 Operator sees a matched record's table view
After a search matches exactly one record (or the operator follows a
relation to exactly one related record), the operator sees a bordered
panel: the table name as a header, and one row per configured column
showing that column's name and value. The field the operator has
selected (via Up/Down) is visually distinguished from the rest, and a
relation field's value is shown as `<related table name>[<foreign key
value>]`.

### 6.4 Operator sees a match/selection list
When a search or relation lookup matches more than one record, the
operator sees the resulting candidates drawn one per row, with the
currently highlighted candidate visually distinguished from the rest.

### 6.5 Operator sees an error notice
When a search or relation lookup fails, the operator sees a modal box
describing the problem, which remains visible until they press Return.

### 6.6 Switching between screens leaves no stale content
As the operator moves from one screen to another (e.g. dismissing the
search dialog into a table view, or a table view into an error notice),
only the newly active screen is visible — nothing from the screen that
was replaced remains on screen.

## 7. Functional requirements

### Drawing the search selection dialog
1. The system must draw the search selection dialog as a modal box
   listing every table/column search pair.
2. The system must visually distinguish the currently highlighted pair
   from the other pairs in that dialog, using reverse video.
3. If there are more search pairs than fit within the dialog's modal, the
   system must scroll the list to keep the highlighted pair visible,
   consistent with how the match/selection list scrolls.

### Drawing the search value prompt
4. The system must draw the search value prompt as a modal box showing
   the selected table/column label and the value typed so far, updating
   as the operator types.

### Drawing the table view
5. The system must draw a matched record's table view as a bordered
   panel with the table name shown as a header.
6. The system must draw one row per configured column of that table,
   showing the column's name and its value.
7. The system must visually distinguish the currently selected field
   from the other fields in that panel, using reverse video.
8. The system must render a relation field's value in the
   `<related table name>[<foreign key value>]` format within the drawn
   panel.

### Drawing the match/selection list
9. The system must draw a match/selection list as a modal box (the same
   visual family as the search selection dialog), with each candidate
   record as its own row.
10. The system must visually distinguish the currently highlighted
    candidate row from the other rows, using reverse video.

### Drawing the error notice
11. The system must draw the error notice as a modal box describing the
    problem.
12. The system must keep the error notice visibly drawn until the
    operator dismisses it.

### Screen consistency
13. The system must ensure that only the currently active screen is
    visibly drawn at any point — no content from a previously active
    screen remains visible once a new screen becomes active.

### Terminal size handling
14. The system must redraw the currently active screen to fit the
    terminal's new size whenever the terminal window is resized while
    dbbro is running.
15. If a line of content (a table view row, a modal's text) is wider than
    the terminal's current width, the system must truncate that content
    to fit rather than let the display wrap or corrupt.

## 8. Non-functional requirements

1. The screen must reflect the current state after every key press that
   changes what should be on screen — no perceptible lag between an
   operator's action and the corresponding redraw.
2. The panel and modal borders must use the exact Unicode box-drawing
   characters given in the briefing; dbbro requires a terminal capable of
   rendering them and does not provide a plain-ASCII fallback.
3. The screen must remain correctly sized and drawn after the terminal
   window is resized, with no operator action required beyond the resize
   itself.

## 9. Acceptance criteria

### Drawing the search selection dialog
- AC1. Given the search selection dialog is open, dbbro draws a modal box
  listing every table/column search pair from the configuration.
- AC2. Given the search selection dialog is open, the currently
  highlighted pair is drawn in reverse video relative to the others.
- AC3. Given more search pairs exist than fit within the dialog's modal,
  the list scrolls to keep the highlighted pair visible, the same way the
  match/selection list scrolls.

### Drawing the search value prompt
- AC4. Given the search value prompt is open, dbbro draws a modal box
  showing the selected table/column label and the currently typed value,
  and the drawn value updates as the operator types.

### Drawing the table view
- AC5. Given a matched record's table view is displayed, dbbro draws a
  bordered panel with the table name as a header.
- AC6. Given that panel, dbbro draws one row per configured column,
  showing each column's name and value.
- AC7. Given that panel, the currently selected field is drawn in reverse
  video relative to the other fields.
- AC8. Given a relation field within that panel, its value is drawn in
  the `<related table name>[<foreign key value>]` format.

### Drawing the match/selection list
- AC9. Given a match/selection list is displayed, dbbro draws it as a
  modal box, with each candidate record as its own row.
- AC10. Given that list, the currently highlighted row is drawn in
  reverse video relative to the other rows.

### Drawing the error notice
- AC11. Given an operation has failed, dbbro draws the error notice as a
  modal box describing the problem.
- AC12. Given the error notice is displayed, it remains visibly drawn
  until the operator presses Return.

### Screen consistency
- AC13. Given the operator moves from one screen to another, no visible
  content from the screen that was replaced remains on screen once the
  new screen is drawn.

### Terminal size handling
- AC14. Given the terminal window is resized while dbbro is running, the
  currently active screen is redrawn to fit the new size.
- AC15. Given a line of content wider than the terminal's current width,
  dbbro truncates that content to fit rather than letting the display wrap
  or become corrupted.

## 10. Dependencies and assumptions

- Depends on EP-2 (Record Search) for the search selection dialog and
  search value prompt's existence and state (highlighted pair, typed
  value) — this epic only draws what EP-2 already decides.
- Depends on EP-3 (Entry Table View) for the table view's existence and
  state (selected field, relation formatting) — this epic only draws it.
- Depends on EP-5 (Error Reporting) for the error notice's existence and
  state (the message to show, when it is dismissed) — this epic only
  draws it.
- Does not depend on EP-4 (Browsing History), since history navigation
  redisplays a table view that already exists and is already drawn by
  this epic's table-view rendering.
- Assumes the exact box-drawing character sets given in
  `specs/briefing.md`'s "Characters" section are the required visual style
  for panels and modals.

## 11. Open questions

_None outstanding — all Cycle 1 questions were resolved; see decision log._

## 12. Decision log

### Cycle 1 — answered
| #  | Question | Decision |
| -- | -------- | -------- |
| Q1 | How should the currently highlighted/selected item be visually distinguished? | Reverse video (swapped foreground/background colors) |
| Q2 | Should the search selection dialog scroll when there are more pairs than fit? | Yes — scroll, the same way the match/selection list already scrolls |
| Q3 | Should the match/selection list be drawn as a modal or a panel? | Modal (double-line border), the same visual family as the search selection dialog |
| Q4 | What should happen on terminal resize while running? | Redraw the current screen to fit the new terminal size |
| Q5 | What should happen if content is wider than the terminal? | Truncate the content to fit |
| Q6 | Should dbbro require Unicode box-drawing support, or fall back to ASCII? | Require Unicode support; no ASCII fallback is defined |
