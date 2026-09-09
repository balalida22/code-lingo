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
