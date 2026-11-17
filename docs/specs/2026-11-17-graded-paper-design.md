# "Graded Paper" visual design — frontend skin

Date: 2026-11-17
Owner-provided design brief. The IDE-workspace layout (activity rail, file tree,
editor, inspector, status bar) stays; this replaces the skin.

## Palette

Role | Hex
--- | ---
Paper (background) | #F3EEE3
Card surface | #FBF8F1
Ruled lines / borders | #D9D1BF
Ink (text) | #1C1B19
Graphite (muted text) | #6F6A5F
Accent: fountain-pen cobalt | #2638C4
Accent hover | #1B2A9B
Code panel (dark island) | #17161A

Severity (stamp colors):

Severity | Hex
--- | ---
Critical, vermilion | #C8281E
High, burnt orange | #D9622B
Medium, mustard | #C99A12
Low, graphite | #7C7A72

Score: good #2F6B4F (forest), mid #C99A12 (mustard), bad #C8281E (vermilion).
Diff: added #CFE8B8 (highlighter green), removed #F6C9C0 (pink-red).

Dark mode (optional, not in v1): warm charcoal bg #16140F, surface #1F1C16,
text #ECE6D8, accent #8FA2FF, border #352F25.

## Fonts

- Headings: a serif — Fraunces or Newsreader (Google Fonts)
- UI: IBM Plex Sans
- Code: JetBrains Mono
- Skip Inter entirely.

## Signature details (what makes it un-generic)

1. Severity badges as rubber stamps: square-ish, uppercase, 1.5px border,
   rotated about -2deg.
2. Flagged lines in the editor get a wavy red-pen underline under the problem
   line, not a plain red background.
3. Score dial: a circled grade ("72") drawn in red pen with a slightly
   imperfect ring.
4. Faint ruled-notebook line texture on the landing page only.
5. Code panel stays dark (#17161A) so it pops against the paper like a
   terminal on a desk. Warm syntax colors: sand, sage, rust, dusty blue.

## CSS variables

```css
:root {
  --paper: #F3EEE3;
  --card: #FBF8F1;
  --rule: #D9D1BF;
  --ink: #1C1B19;
  --graphite: #6F6A5F;
  --accent: #2638C4;
  --accent-hover: #1B2A9B;
  --code-bg: #17161A;
  --critical: #C8281E;
  --high: #D9622B;
  --medium: #C99A12;
  --low: #7C7A72;
  --good: #2F6B4F;
  --diff-add: #CFE8B8;
  --diff-del: #F6C9C0;
}
```
