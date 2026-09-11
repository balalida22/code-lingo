# Code Lingo v1.4.0 — prepared update

- Add dedicated NumPy, Matplotlib, PyTorch, and Transformers tracks: each has
  12 lessons and 144 exercises across three sections, with 25-question exams.
- Preserve original Python samplers and all previous course banks/history.
- Rename the course picker action to Change language / library; sampler lessons
  point learners toward their deeper library track.
- Add contextual Python AST matching for writing fragments, supporting slices,
  operators, keyword arguments, and equivalent whitespace without execution.
- 97 regression tests pass. Native NumPy/Matplotlib audit passes 291 sampled
  output/repair programs; PyTorch and Transformers runtimes are unavailable.

---

# Code Lingo v1.3.0 — prepared update

- Add Java, Go, C#, Bash, Kotlin, and Swift: 20 lessons and 240 exercises each,
  across Basics, Intermediate, and Advanced. No specialized framework tracks.
- Teach native contracts: JVM APIs, Go concurrency, C# disposal/LINQ,
  Bash expansion/processes, Kotlin nullability/extensions, and Swift ARC/actors.
- Reuse language selection, pins, 25-question exams, and spaced review;
  preserve all existing course banks and learning history.
- Add native Bash/Java output auditing and regression coverage for new tracks.
- 92 tests pass, including complete learning/exam flows for the new languages.
  Native audit: 146 Bash and 132 Java variants pass; the Java 21 virtual-thread
  example and Go/C#/Kotlin/Swift were not compiled in this environment.

---

# Code Lingo v1.2.0 — prepared update

- Schedule successfully learned, practiced, and examined questions for spaced review.
- Review after 1 day, then 3, 7, 14, and 30 days following due successes; mistakes
  still return after 10 minutes. Early review preserves the due date.
- Backfill existing learned history without resetting progress or mistake schedules.
- Show due counts in both menus and use learned questions in lesson warm-ups.
- Remove the fixed scenario count; expand four Rust lessons to 18 questions
  (336 Rust exercises total). Retain all existing question IDs and completions.
- 88 tests pass. Rust compiler unavailable; new examples reviewed against the
  Rust Book chapters on borrowing, lifetimes, smart pointers, and shared state.

---

# Code Lingo v1.1.2 — prepared update

C/C++ writing answers now accept formatting such as `x + 6` and `x+6` as the
same construction. Whitespace within literals and changes to tokens still
matter. No learner code is compiled or executed. Commands and preprocessor
fragments keep exact matching. Existing progress and question IDs are retained.

84 automated tests pass, including grading and heart-deduction regressions.

---

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
