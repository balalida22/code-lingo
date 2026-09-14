# Changelog

## 1.6.0 — prepared, not published

- Add streak recovery for gaps of one or two missed local calendar days.
- Require two distinct finished lessons/exams and ten distinct correctly reviewed
  questions per missed day, completed on the return day across any courses.
- Add a recovery menu with lesson/review shortcuts and progress, plus the
  `recover-streak` command to inspect targets or claim a completed repair.
- Persist repaired dates separately: no fabricated lesson completions, EXP,
  daily-goal credit, or curriculum unlocks. Claims are transactional and idempotent.
- 122 regression tests pass, including one/two-day gaps, target deduplication,
  invalid gaps, restart persistence, and continuation after recovery.

## Unreleased

- Organize detailed guides under `docs/`, add a documentation index, and update
  relative links and the generated curriculum destination.

## 1.5.1 — prepared, not published

- Practice now restores one heart per five correct answers instead of every answer.
- Save partial heart progress across sessions and courses; mistakes do not reset it.
- Show progress toward the next heart and a message when a heart is earned.
- Do not bank correct practice answers while hearts are full.
- 113 regression tests pass. Existing review rewards and exam rules are unchanged.

## 1.5.0 — prepared, not published

- Add Overall analytics to both menus, with an all-course overview and filters
  limited to courses with saved activity; filtering does not switch learning courses.
- Draw terminal bar charts for lesson completion, accuracy by mode, and daily
  answer counts over seven local calendar days, including days with no activity.
- Report answer-weighted accuracy, unique questions seen, reviews due, and
  passed/finished exams. Count section-exam lesson completions without counting
  unfinished exams as finished; retain visibility of older/custom course history.
- Add `analytics` and `analytics --filter COURSE_ID` commands. No database migration.
- 108 regression tests pass, including filter isolation, read-only aggregation,
  empty history, date boundaries, and scrolling in a 60×18 terminal.

## 1.4.1 — prepared, not published

- Browse sections first, then only the lessons in the selected section, in both menus.
- Show section status and completed lesson counts; preserve locked-lesson explanations.
- Initially select the active lesson or first open lesson and center scrolling menus.
- After a session, focus the next available lesson; Back returns to the section picker.
- Keep course banks, saved progress, and main-menu section exams unchanged.
- 101 regression tests pass, including section navigation and centered scrolling.

## 1.4.0 — prepared, not published

- Add dedicated NumPy, Matplotlib, PyTorch, and Transformers tracks: each has
  12 lessons and 144 exercises across three sections, with 25-question exams.
- Preserve original Python samplers and all previous course banks/history.
- Rename the course picker action to Change language / library; sampler lessons
  point learners toward their deeper library track.
- Add contextual Python AST matching for writing fragments, supporting slices,
  operators, keyword arguments, and equivalent whitespace without execution.
- 97 regression tests pass. Native NumPy/Matplotlib audit passes 291 sampled
  output/repair programs; PyTorch and Transformers runtimes are unavailable.

## 1.3.0 — prepared, not published

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

## 1.2.0 — prepared, not published

- Schedule successfully learned, practiced, and examined questions for spaced review.
- Review after 1 day, then 3, 7, 14, and 30 days following due successes; mistakes
  still return after 10 minutes. Early review preserves the due date.
- Backfill existing learned history without resetting progress or mistake schedules.
- Show due counts in both menus and use learned questions in lesson warm-ups.
- Remove the fixed scenario count; expand four Rust lessons to 18 questions
  (336 Rust exercises total). Retain all existing question IDs and completions.
- 88 tests pass. Rust compiler unavailable; new examples reviewed against the
  Rust Book chapters on borrowing, lifetimes, smart pointers, and shared state.

## 1.1.2 — prepared, not published

- Accept whitespace differences between tokens in C/C++ writing answers.
- Preserve literal contents, identifiers, operators, and exact command/directive checks.
- Keep question IDs and history; update writing instructions.
- Six new regressions cover spacing, token boundaries, literals, and heart deductions.

## 1.1.1 — prepared, not published

- Dim routine prompts and navigation, and highlight lesson explanations in bold cyan.
- Persist language pins, sort them first, and preserve selection when toggling.
- Add p to pin/unpin in the TUI and p NUMBER in the line-input picker.
- Remove the text-line counter; show a scroll hint only when content overflows.
- Add five UI/persistence regressions; 78 tests pass.

## 1.1.0 — prepared, not published

- Expanded C, C++, TypeScript, vanilla web, Ruby, Lua, SQL, PHP, and Perl from
  14 to 20 lessons each, adding 54 lessons and 648 exercises.
- Native prerequisite orders and language-specific runtime/API boundaries.
- Error-reading questions now lead to successful code repairs in these courses.
- Preserved all existing lesson IDs and the meaning of retained exercise IDs;
  retired completion exercises remain in stored history, with new IDs for repairs.
- Added a v1 identity fixture, history/resumption regressions, primary-reference
  mappings, and an optional native audit including a Lua 5.4 shared-library runner.
- Python and Rust course banks remain unchanged. No new specialized tracks.

## 1.0.0 — 2026-09-09

First major release of Code Lingo. Promotes the reviewed 0.3.1
implementation to v1.0.0, with GitHub CI, source-control exclusions, and release
notes. No course or gameplay behavior changes are introduced by this version bump.

See [RELEASE_NOTES.md](docs/RELEASE_NOTES.md) for the release features and validation.

## 0.3.1

- Green correct and red incorrect feedback titles.
- Rust Book-led curriculum: 26 lessons and 312 exercises.
- Error diagnosis followed by code-repair exercises.
- Chapter-specific references and optional native Rust audit.
- Correct counts when retired lesson IDs remain in historical progress.

## 0.3.0

- Added ten language courses and a persistent language picker.
- Independent lesson, exam, and mistake progress by course.

## 0.2.x

- uv-managed environment and arrow-key TUI.
- Randomized CLQ exercise templates and expanded lessons.
- Section placement exams, progress counters, and course status colors.
- Daily goal based on finishing a lesson or exam.
