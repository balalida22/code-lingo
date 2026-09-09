# Code Lingo v1.1.1 — prepared update

- Routine prompts and navigation are dimmed; lesson explanations are bold cyan.
- Press **p** in the language picker to pin/unpin a language. Pins appear first
  with a star and persist across restarts. The line-input picker uses `p NUMBER`.
- Removed the confusing text-line counter. A scroll hint appears only when
  there is more text than fits on screen.
- 78 regression tests pass; language banks and existing learning history are unchanged.

---

# Code Lingo v1.1.0 — prepared update

This source update extends the Rust-style native curriculum review to C, C++,
TypeScript, vanilla HTML/CSS/JavaScript, Ruby, Lua, SQL, PHP, and Perl.

- 54 new lessons and 648 added exercises; 224 lessons and 2,688 exercises total.
- Each revised track now contains 20 lessons and 240 exercises, with its own
  prerequisite order and practical language/platform boundaries.
- Error-reading questions lead into successful code-repair exercises.
- Existing lesson completion and stored history are preserved; new topics and
  repair cards start unfinished. Exams remain 25 questions and cost no hearts.
- Python and Rust banks remain unchanged; no new specialized tracks.
- 73 regression tests, 870 sampled native output/repair programs, and 12 expected
  TypeScript type failures pass. Ruby, PHP, and browser-dependent behavior have
  not been native-executed here.

See [NATIVE_CURRICULA.md](NATIVE_CURRICULA.md) for topic changes, references,
compatibility, and validation scope, and [README.md](README.md) to run with uv.

---

# Code Lingo v1.0.0

Code Lingo is a reading-first programming language tutor for the terminal.
Learn to understand code before writing it, with short daily lessons,
randomized questions, and spaced review of mistakes.

## Included in this release

- 11 courses, 170 lessons, and 2,040 exercises.
- Python, C, C++, Rust, TypeScript, vanilla HTML/CSS/JavaScript, Ruby, Lua,
  SQL (SQLite), PHP, and Perl.
- Rust follows the Rust Book across 26 lessons and 312 exercises, including
  ownership, borrowing, lifetimes, Cargo, testing, smart pointers, concurrency,
  async semantics, and useful CLI work.
- Twelve exercises per lesson: eight reading MCQs, then four writing exercises.
- Section exams with 25 questions; a score above 80% marks the section complete.
- Arrow-key TUI, green/red feedback titles, and live correct/wrong/remaining counts.
- Hearts, EXP, gems, combos, daily completion goals, and a mistake notebook.
- Per-language progress and remembered course selection.
- A plain line-input interface and uv-managed environment.

## Run

Download and extract the source archive, then open a terminal in its directory:

```bash
uv sync --locked
uv run python -m codelingo
```

Choose **Change language** to select a course. Use `menu` for the line-input UI.
The application has no third-party Python runtime dependencies; it uses curses
where available. It never executes learner submissions or requires the taught
language runtimes to be installed.

## Verification and current limits

The release passes 69 automated tests. Green/red feedback and navigation have
also been exercised in a real terminal. Course answers are checked using Python
ASTs for Python writing and explicit fragments for other languages; this is not
an arbitrary-program equivalence checker.

Native Rust compilation was unavailable during preparation. An optional
`uv run python tools/verify_rust.py` audit is included for Rust 1.90+ environments.
Other native verification coverage is documented in README.md and RUST_BOOK.md.
New languages have no specialized framework/library tracks; Python retains its
existing specialized lessons.

## Progress and licensing

Existing progress databases migrate in place. Unchanged lesson identities retain
completion, while new or replacement Rust topics begin unfinished. Previously
earned rewards and stored history are preserved.

Software: MIT. Course prose and exercise banks: CC BY 4.0.
See LICENSE and SOURCES.md for the scope and source acknowledgments.
