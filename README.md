# Code Lingo 1.1.1

**Read code. Build fluency. A little every day.**

A programming language tutor with an arrow-key terminal interface, daily progress,
randomized exercises, spaced mistake review, and exams for skipping sections.

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for the prepared v1.1.1 update and
[CHANGELOG.md](CHANGELOG.md) for the project history.

## Run with uv

[Install uv](https://docs.astral.sh/uv/getting-started/installation/), clone the
repository or extract its source archive, and open a terminal in the project
directory:

```bash
uv sync --locked
uv run python -m codelingo
```

The default interface is the full-screen TUI when launched in an interactive
terminal. Use **↑/↓** to select, **Enter** to confirm, and **Esc** to go back.

- **Top left:** EXP and gems.
- **Top center on the main menu only:** streak and daily goal.
- **Top right:** hearts.
- **Top center during lessons and exams:** replaces the daily stats with a live
  problem-progress bar and correct/wrong/remaining
  counts, e.g. `10/2/13`. Correct is green, wrong is red, and remaining uses the
  default color. This tracks the current lesson, review, practice, or exam—not
  the separate one-lesson-or-exam daily goal. Resuming a lesson restores its counts.
- The bar shows distinct problems answered. A retry changes a red problem to
  green when corrected; it never inflates the total. At 100% answered, any red
  problems still need correction before a learning lesson is complete.
- **Course colors:** green DONE, cyan OPEN, yellow ACTIVE, red LOCK. Selecting
  a locked lesson or exam explains its prerequisites and returns to the picker.
- **PgUp/PgDn:** scroll long code, teaching notes, or explanations.
- **Writing:** type the requested fragment; left/right, Home/End, Delete, and
  Backspace edit it.
- **Reading emphasis:** routine instructions and navigation are dimmed; answer
  explanations use bold cyan, with green/red feedback titles retained.
- **Scrolling:** “More text · PgUp/PgDn” appears only when text overflows.
  The old “text line” counter is removed.
- **Hints:** `?` in reading; enter `?` in writing.
- **Skip a question:** `s` in reading; enter `:skip` in writing.

The TUI uses Python's standard `curses` module, included in most Linux/macOS
Python distributions. Minimum terminal size is 60 columns × 18 rows; 80 × 24
or larger is more comfortable. Python builds without curses can use the
line-input interface:

```bash
uv run python -m codelingo menu
```

`.python-version` selects Python 3.12 and `uv.lock` records the project. uv
creates `.venv` and may download Python if the selected interpreter is absent.
The application has **no third-party runtime dependencies**. Once Python and
uv are present, `uv sync --locked --offline` works without the network.
`[tool.uv] package = false` makes this a source-run application: use
`uv run python -m codelingo`, not `uv run code-lingo`. Nothing needs activation.

## What changed

- **11 courses, 224 lessons, and 2,688 exercises** in total.
- **Rust follows the Rust Book:** 26 lessons × 12 exercises = 312 exercises,
  split into 8 Basics, 9 Intermediate, and 9 Advanced lessons.
- The other nine added languages now have **20 lessons × 12 exercises** each.
  Their native topics and prerequisite order are documented in
  [NATIVE_CURRICULA.md](NATIVE_CURRICULA.md): C compilation and memory contracts,
  C++ value semantics, TypeScript runtime boundaries, browser behavior, Ruby
  protocols, Lua embedding, PHP requests, Perl text processing, and SQLite semantics.
- Each lesson has 8 reading MCQs followed by 4 writing exercises.
- Correct feedback titles are **green**; incorrect feedback titles are **red**.
  Text labels remain explicit when color is unavailable.
- Python retains its 18 lessons and 216 exercises, including its existing
  specialized tracks. New courses have no specialized library tracks.
- New numerical values, strings, and contexts on template encounters; answers,
  distractors, and explanations are generated together.
- **25-question section exams** with a strict **>80%** threshold: **21/25 passes;
  20/25 does not**.
- Full-screen keyboard navigation and a persistent, updating status bar.
- Earnable gems and a small heart-recovery shop.
- Additive database migration that retains existing progress.

## Choose a language

Select **Change language** on the TUI main menu (or option 10 in the line menu).
The menu displays each course's completion count and highlights the active
course. Press **p** to pin/unpin the highlighted language. Pinned languages
show **★**, appear first, and persist across restarts. With pins present, the
picker opens at the top of the pinned group. The line-input picker supports
`p NUMBER` and shares the same pins. Your last selected built-in language is remembered across launches.
Lessons, exam passes, resumable sessions, and mistakes are separate by course;
EXP, gems, hearts, and the daily goal belong to the shared profile.

```bash
uv run python -m codelingo languages
uv run python -m codelingo --course rust
uv run python -m codelingo --course cpp exam Basics
uv run python -m codelingo --course web course
```

| Course ID | Course | Baseline |
| --- | --- | --- |
| `python` | Python (existing course) | Python 3 |
| `c` | C | C17 |
| `cpp` | C++ | C++20 |
| `rust` | Rust | Rust 1.90+, edition 2024 |
| `typescript` | TypeScript | Strict checking, ES2022 target |
| `web` | Vanilla HTML + CSS + JavaScript | Standards-mode browser; no frameworks |
| `ruby` | Ruby | Ruby 3.x |
| `lua` | Lua | Lua 5.4 |
| `sql` | SQL | SQLite 3.35+ dialect |
| `php` | PHP | PHP 8.2+ |
| `perl` | Perl | Perl 5, strict and warnings |

See [CURRICULA.md](CURRICULA.md) for every lesson. All new courses focus on
reading and writing language features; there are no algorithm or data-structure
implementation lessons. Ordinary use of native arrays, maps, and standard
language types remains part of learning the syntax.

## Language-native revisions

Rust now follows its own progression: Cargo and immutable bindings, ownership
and borrowing, UTF-8 and domain modeling, recoverable errors, generic and borrowed
APIs, then tests, useful CLI boundaries, smart pointers, concurrency, and async.
See [RUST_BOOK.md](RUST_BOOK.md) for the chapter-to-lesson map and validation scope.
The standard library is included; third-party runtime/framework tracks are not.
The 1.1.0 revision extends this approach to the other nine added languages with
54 new lessons and diagnosis-to-repair sequences. Python's existing idiomatic
course and Rust's Book-led course are unchanged. No new specialized tracks or
algorithm/data-structure implementation lessons are added.

Existing EXP, gems, streaks, and stored history survive. Retained lesson IDs keep
their completion state; new lessons start unfinished. Replaced question families
receive new IDs, while old attempts remain stored. The language picker counts
only lessons in the current curriculum. Retake a section exam or study its new
lessons to complete the expanded section; an old exam pass does not automatically
mark new topics learned. Previous first-pass exam bonuses remain claimed.

## Everyday use

```bash
uv run python -m codelingo                   # TUI in a terminal
uv run python -m codelingo tui               # explicitly launch TUI
uv run python -m codelingo learn             # line-input lesson / resume
uv run python -m codelingo --course python learn numpy       # choose an unlocked lesson
uv run python -m codelingo course            # course map and prerequisites
uv run python -m codelingo review            # due mistakes
uv run python -m codelingo review --all       # include upcoming mistakes
uv run python -m codelingo practice          # practice and restore hearts
uv run python -m codelingo exam Basics       # skip-section exam
uv run python -m codelingo mistakes          # exact past mistakes
uv run python -m codelingo stats             # progress and recent exams
uv run python -m codelingo sources           # curriculum provenance
uv run python -m codelingo demo              # scripted, temporary-profile tour
```

In the TUI, choose **Skip section · take exam** to test out of a section.
Global options go before the command:

```bash
uv run python -m codelingo --data-dir ./another-profile tui
uv run python -m codelingo --seed 7 learn
uv run python -m codelingo --plain
```

`--seed` is for repeatable testing. Normal play uses fresh randomness. In
line-input mode, option letters/numbers are accepted; `:q` leaves the session.
Invalid selection syntax does not cost a heart. `NO_COLOR` disables ANSI
styling in the line-input interface.

## Section exams

Each exam samples **25 distinct problem IDs**, balancing the number contributed
by each lesson. Every lesson contributes both reading and writing. Questions
and options are shuffled, and parameterized questions draw new values.

- Complete the entire exam in one session. Answers persist as they are submitted,
  but leaving abandons the exam and a later attempt starts fresh.
- There are no hints or retries. Live correct/wrong/remaining counts update after
  each submission; detailed answers and explanations appear at the end.
- Hearts do not limit or penalize placement exams.
- **21 correct answers or more passes**. Integer arithmetic enforces the strict
  threshold; there is no rounding of 80% into a pass.
- Passing marks every lesson in the section **DONE** in green, unlocking subsequent
  prerequisites. It does not pretend that every individual card was practiced.
- A first pass awards **50 EXP and 20 gems**. Retakes cannot farm this bonus.
- Mistakes enter the notebook and review schedule. Feedback appears at the end.
- Prerequisites from other sections must already be completed or passed by exam.
  For example, pass Basics before taking Intermediate, then pass Intermediate
  before Advanced. Python also has its original Specialized section.

A completed exam counts toward the daily goal whether it passes or fails.
Passing additionally awards the section bonus; exam answers do not earn per-card
EXP. An interrupted process cannot unlock a section or satisfy the daily goal
from a partial exam.
Exam history shows abandoned/unfinished attempts as well as complete results.

## Reading, writing, and randomness

Each lesson starts with teaching notes. Eight reading questions cover output,
control flow, API interpretation, and common mistakes. All must be answered
correctly before four short writing exercises open. Incorrect answers requeue
within that stage. Every answer is saved, so `learn` resumes unfinished work.

The **CLQ v2** format lives in `codelingo/courses/python.json`. It combines typed
parameter samplers, bounded derived expressions, and `${placeholder}` text.
For example, a multiplication problem samples its operands and recomputes the
correct result, plausible wrong results, and explanation as one unit. Numeric
ranges and string pools can be changed without rewriting the question.

A template keeps a stable concept/question ID while its concrete values vary.
The review scheduler tracks that ID and generates a fresh variant for practice;
the notebook saves the exact old code, options, answer, and explanation. The
sampler avoids immediately repeating the previous concrete variant where
possible. It also rejects duplicate MCQ choices.

The 90 original curated questions remain useful for rules and misconceptions;
not every question needs a different arithmetic answer. The new 126 templates
add variation, but literal randomization alone does not prove transfer to real
codebases. More structural variants and repository excerpts are still useful
future curriculum work.

Writing checks parse the requested fragment and compare it to listed accepted
syntax trees. Formatting and quote style can vary, but arbitrary semantically
equivalent programs are not recognized. Prompts specify the requested form.
Neither learner code nor displayed lesson code is executed by the tutor.

## Course map

| Section | Lessons | Problems | Focus |
| --- | ---: | ---: | --- |
| Basics | 5 | 60 | Names/output, arithmetic, input/types, strings, conditions |
| Intermediate | 5 | 60 | Python collection syntax, loops, functions, imports, exceptions |
| Advanced | 4 | 48 | Aliasing/defaults, classes, generators, decorators/async |
| Specialized | 4 | 48 | NumPy, Matplotlib, PyTorch, Transformers |

These are starter language/library lessons, not comprehensive library courses.
Algorithms, complexity analysis, and data-structure implementation remain out
of scope. Collections appear as Python syntax and API usage.

## Rewards and review

| Mechanic | Rule |
| --- | --- |
| Hearts | 5 maximum; wrong learning/practice/review answers and skips cost 1, floored at 0 |
| Recovery | 1 heart per 30 minutes; a correct practice/review answer restores 1 |
| Zero hearts | New learning pauses; practice, review, and exams remain available |
| EXP | 10 base; combo bonus +5 at 3 consecutive correct, +10 at 6, +15 at 9+ |
| Gems | 2 per newly credited correct problem; 20 for the first pass of each section exam |
| Shop | Spend 10 gems to restore 1 heart; full hearts and insufficient funds spend nothing |
| Credit limit | One EXP/gem credit per problem ID per local day, regardless of variants |
| Daily streak | Finish one lesson, full lesson replay, or exam to secure the day |
| Mistakes | First review due after 10 minutes; due successes schedule 1, 3, 7, 14, then 30 days |
| Lapse | A later wrong answer restarts the 10-minute interval |
| Early review | Can restore a heart, but does not postpone the existing due date |

## Daily completion goal

The main menu shows `0/1 today` until you finish one lesson or exam, then
`1/1 today`. Individual correct answers and short practice/review sessions earn
EXP and gems as usual, but do not satisfy this goal. A full exam counts even
if it fails; passing above 80% is still required to unlock its section.

Selecting an already-completed lesson replays all 12 problems. Finishing the
whole replay counts toward the daily goal; leaving partway through does not.
A lesson is counted at most once per local date, while separate finished exams
are separate completions. The header caps the goal at `1/1`; Stats shows the
number of completions. New lessons are credited on the last correct submission,
even if you leave the feedback page immediately.

Earlier earned streak days are preserved during migration. Today's old
five-question credit does not substitute for completing a lesson or exam;
recorded lesson/exam completions are recognized. Completions count on the local
date they finish, including sessions that cross midnight.

## Existing progress and privacy

The default database remains `$XDG_DATA_HOME/code-lingo/progress.sqlite3`, or
`~/.local/share/code-lingo/progress.sqlite3`. `CODELINGO_HOME` and `--data-dir`
override it. No accounts, API calls, downloads of models, or cloud sync occur.

Version 0.1 databases migrate in place by adding fields and tables. Existing
EXP, hearts, completions, and mistakes survive; gems start at zero. Old completed
lessons remain completed even though more exercises have been added, and their
expanded content is available through practice. Earlier mistakes lack a saved
variant snapshot and use their original static question. Close the app before
copying the SQLite file for a backup.

## Development and verification

```bash
uv sync --locked
uv run python -m codelingo validate
uv run python -m unittest discover -s tests -v
# Optional, with native compilers/interpreters installed:
uv run python tools/verify_native.py
# Optional Rust audit with rustc 1.90+ installed (no crate downloads):
uv run python tools/verify_rust.py
```

78 tests cover all new lesson and exam completion paths, 30 sampled variants of
every new template, language selection and persistence, independent mistakes,
SQLite query results, and the existing Python/gameplay/UI regression suite.
Separate compiler/interpreter checks passed for 870 sampled authored predictions
and repaired programs across C, C++, Lua 5.4, Perl, TypeScript, JavaScript, and SQLite.
Twelve expected TypeScript type failures were also verified with TypeScript 5.6.3.
SQLite regression checks also cover all 80 reading scenarios at three seeds,
including expected constraint failures. Ruby and PHP executables
were unavailable, so those revisions received schema/variant and reference-based
review rather than native execution. DOM/CSS examples were reviewed against MDN;
a browser runtime was unavailable. Rust remains unchanged and its optional audit
still requires rustc. See [NATIVE_CURRICULA.md](NATIVE_CURRICULA.md) for scope.

The real TUI was also checked for arrow navigation, language switching, course
map access, persistence of the selected course, and clean exit. Correct/incorrect title colors and reset to a neutral title
were also verified in a real terminal.

The generated banks are intentionally scaffolded: each lesson studies four
scenarios through prediction, choosing a missing code fragment, and writing a
fragment. Those stages sample literals independently. Error-reading scenarios
in Rust and the nine expanded courses lead to writing repairs of the broken code.
Fixed conceptual cards remain fixed when random numbers would not improve the question. Non-Python
writing uses exact fragments (outer whitespace is ignored); it does not attempt
to accept every semantically equivalent program. The app never executes learner
input and does not need the taught languages installed.

The code remains separated into course/templates, persistence, exams, line CLI,
and TUI modules. See `COURSE_AUTHORING.md` for CLQ and `SOURCES.md` for provenance.
Code is MIT licensed; course prose/exercises are CC BY 4.0. No affiliation with
Duolingo or source-course providers is implied.
