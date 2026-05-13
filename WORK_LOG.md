# EC22 Lecture 2 Work Log

Date: 2026-05-13

## Summary

This note records the setup, fixes, graph generation, LaTeX compilation, and GitHub upload completed for the EC22 Lecture 2 macro variables materials.

## Stata Project Setup

- Located the project at `/Users/alessiaroot/econ22/EC22_start`.
- Identified the master Stata runner as `EC22Data/Lecture2_Macro Variables.do`.
- Ran Stata from `EC22Data` using the installed StataNow executable:
  - `/Applications/StataNow/StataSE.app/Contents/MacOS/stata-se`
- Created temporary project-local compatibility runners because the original do-files used Windows-style paths and a filename with spaces.
- Installed required Stata add-ons locally inside the project rather than changing the global Stata setup:
  - `scheme-modern`
  - `nbercycles`

## Data And Graph Generation

- Used a FRED API key temporarily for Stata `import fred` calls.
- Removed the key from runner files after each run and scrubbed logs.
- FRED intermittently returned I/O/server errors, so the Stata work was completed in pieces rather than one uninterrupted run.
- Generated the completed graph outputs in:
  - `EC22Data/Graphs/`
- Completed sections include:
  - inflation
  - GDP annual
  - GDP NIPA annual
  - Okun
  - unemployment
  - employment
  - LFPR
  - labor share
- Skipped `trump_tweet.do` after repeated FRED I/O errors, per instruction.

## LaTeX Compilation

- Created a combined LaTeX source:
  - `Lecture2_Macro_Variables/compiled_graphs_and_slides.tex`
- Compiled the combined PDF:
  - `Lecture2_Macro_Variables/compiled_graphs_and_slides.pdf`
- The compiled PDF includes:
  - the existing lecture slide deck
  - all generated graph PDFs
- Final compiled output:
  - 177 pages
  - about 2.7 MB

## GitHub Upload

- Fixed the local Git remote URL from `hithub.com` to `github.com`.
- Added a `.gitignore` to avoid committing temporary build products, raw data, Stata add-ons, logs, and temporary Codex runner files.
- Committed the lecture materials and graph compilation.
- Pulled/rebased onto the existing remote `main` branch to preserve prior repository history.
- Pushed to:
  - `https://github.com/alessiaeroot/ders-26s`

## Key Commit

- `34bea47` - Add lecture 2 slides and graph compilation

