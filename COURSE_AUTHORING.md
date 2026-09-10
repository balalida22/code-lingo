# CLQ v2: Code Lingo question templates

CLQ is a declarative format stored as JSON. A course is an ordered lesson graph;
each question is either a fixed card or a parameterized card. No learner code
or course snippet is evaluated. The format separates **values**, **derived
answers**, and **display text**, so variants remain internally consistent.

Load and validate a custom course:

```bash
uv run python -m codelingo --course-file ./my-course.json validate
uv run python -m codelingo --course-file ./my-course.json tui
```

## Example: a parameterized reading question

```json
{
  "id": "arithmetic-v1",
  "kind": "mcq",
  "concept": "operator-precedence",
  "parameters": {
    "a": {"type": "int", "min": 2, "max": 15},
    "b": {"type": "int", "min": 2, "max": 12},
    "c": {"type": "int", "min": 2, "max": 9}
  },
  "derived": {
    "out": "a + b * c",
    "grouped": "(a + b) * c",
    "sum": "a + b + c",
    "product": "a * b * c"
  },
  "code": "print(${a} + ${b} * ${c})",
  "prompt": "What is printed?",
  "answer": "${out}",
  "options": ["${out}", "${grouped}", "${sum}", "${product}"],
  "hint": "Multiplication has higher precedence.",
  "explanation": "Multiply ${b} by ${c} first, then add ${a}, giving ${out}."
}
```

Change a range once and the shown code, options, and explanation change together.
If a draw creates duplicate distractors, the sampler retries. It raises a clear
error after 100 unsuccessful draws rather than showing an ambiguous question.
The option text is authoritative; option letters are shuffled by the UI.

## Strings and writing

Use a choice sampler for names, strings, identifiers, or contexts. Use `repr`
when putting a string *literal* into Python code: this handles quotes safely.

```json
{
  "id": "greetings-v1",
  "kind": "write",
  "concept": "function-call",
  "parameters": {
    "name": {"type": "choice", "values": ["Ada", "Lin", "Nia", "Kai"]}
  },
  "derived": {"name_py": "repr(name)"},
  "code": "def greet(name):\n    return 'Hi ' + name\n\n____",
  "prompt": "Call greet with positional string ${name_py}.",
  "accepted": ["greet(${name_py})"],
  "checker": "python_ast",
  "hint": "Use ordinary function-call syntax.",
  "explanation": "The argument ${name_py} is supplied to the name parameter."
}
```

`python_ast` is the default writing checker. It accepts syntactic formatting
variants, not arbitrary equivalent implementations. Give multiple `accepted`
constructions where appropriate, or make the prompt specific. Use `exact` for
non-Python writing tasks; it strips surrounding whitespace and compares strings.
MCQs are independent of the programming language.

## Allowed expressions

Derived expressions are interpreted by a small AST visitor; they are never
passed to Python `eval` or `exec`.

- Parameter or previously derived names; constants; lists and tuples.
- `+`, `-`, `*`, `/`, `//`, `%`, unary `+`/`-`, indexing, and slicing.
- Calls to `str`, `repr`, `len`, `sum`, `abs`, `min`, `max`, `round`, `upper`,
  `lower`, and `strip`.
- No imports, attribute access, arbitrary function calls, comprehensions,
  exponentiation, or statements.

Derived values are evaluated in their JSON order. Integer sampler bounds must
stay within -10,000 to 10,000. Expressions have length/AST limits; calculated
numbers and sequence sizes are bounded. Keep snippets short and distractors
plausible. The template renderer transforms `code`, `prompt`, `answer`,
`options`, `accepted`, `hint`, and `explanation` text using `${name}` markers.

## Course and lesson structure

Top-level fields: `schema_version` (2), stable `id`, `title`, `language`, `version`,
`sources`, and `lessons`. Schema version 1 fixed courses are still readable.

Each lesson declares:

- Stable `id`, `title`, and `section` (`Basics`, `Intermediate`, `Advanced`, or
  `Specialized`).
- `intro`: notes teaching the rules needed for the lesson.
- `sources`: source IDs present in the course's `sources` list.
- `requires`: earlier lesson IDs. This ordering makes the graph acyclic.
- `questions`: reading cards first, then writing cards.

Lesson length follows the concepts, with no fixed 12-question cap. Most bundled
lessons have 12 questions; four Rust lessons have 18. The scenario builder accepts
any nonempty scenario list and creates two reading cards and one writing card
per scenario. Keep reading before writing; add original scenarios when a topic
needs more practice rather than duplicating questions. A section
must contain at least 25 distinct cards and each lesson must have both kinds
for placement exams. Exams give each lesson nearly equal representation and
include reading and writing from every lesson.

The validator checks references, required fields, answer membership, distinct
choices, source IDs, stage ordering, and several template draws. It does not
prove the pedagogy or all possible parameter combinations: test meaningful
boundary values and review the explanations. The bundled tests sample 100
variants per template and check selected generated code against Python.

## Identity, history, and review

The stable question ID denotes the exercise family. Do not generate a new ID
for every draw: that would split reviews and allow repeat EXP farming.

When an instance is shown, its concrete fields and sampled values are stored.
When answered, the exact instance is logged with the attempt; the last wrong
instance is retained in the mistake notebook. Future review draws a fresh
variant of the same ID. Correct answers to that ID earn EXP/gem credit only once per day,
regardless of how many variants were seen.

Retain IDs when correcting wording. Use a new ID for a materially different
concept. Legacy completed lessons stay completed when you add cards; their
expanded content is still available through practice. Removed card IDs stay
in the database but are excluded from the active review queue.

Prefer variants that exercise reasoning, not cosmetic changes alone: change
operands, bounds, fallback values, alias names, and call-site arguments while
preserving the language rule being tested. Add different code structures and
realistic contexts as separate cards. Keep algorithm design out of this course.

## Rebuilding the additional languages

The authored scenario sources live in `tools/curricula/`. Run:

```bash
uv run python tools/curricula/build.py
uv run python -m unittest discover -s tests -v
```

This rebuilds the ten new JSON banks without editing Python's bank. Each lesson
has four authored scenarios. Each scenario supplies a prediction MCQ, a code
completion MCQ, and a writing fragment; reading cards precede all writing cards.
Tilde markers surround a single missing fragment in authoring source only;
`__TILDE__` represents a literal tilde in a language snippet. Runtime artifacts
use ordinary CLQ JSON and need none of these authoring modules.

New language writing cards set `checker: "exact"`. They check the named fragment,
including internal spaces, case, literals, and punctuation, with surrounding
whitespace ignored. Python cards continue to use Python AST matching by default.
Do not send other languages' answers to the Python parser. Sources and language
versions belong in each course, and SQLite-specific behavior must be labelled.

The new regression suite samples 30 variants of every card, completes every
course through learning and through section exams, checks course isolation, and
executes all SQL prediction scenarios at three seeds. Native execution checks
for other languages are separate from the app, which never executes code.

## Language-specific curricula and repair stages

Equivalent depth does not require equivalent topic lists or a fixed lesson count.
Rust uses `tools/curricula/rust_course.py`, 26 lessons, explicit section metadata,
and references to individual Rust Book chapters. Run that file to rebuild only
Rust, or `tools/curricula/build.py` to rebuild the complete additional-language set.

A scenario may have an optional `completion` scenario. Its reading prediction
still uses the original code, while its choose/write stages use the completion's
blank, contract, and solution. Use this for error diagnosis followed by repair;
the completion IDs receive a `repair-` prefix. Changed concepts receive new IDs,
so earlier attempts do not incorrectly satisfy a replacement family. Authoring
metadata supports explicit section and source IDs per lesson; default layouts
remain available for other languages. Keep each section at 12 lessons or fewer
if its 25-question exam must sample both reading and writing from every lesson.


## Native curriculum revisions

`tools/curricula/native_revision.py` assembles the nine revised courses from
retained scenarios and the `native_*.py` topic modules. Its explicit section
orders determine prerequisites; do not impose the Python topic order on a new
language. `build.py` also regenerates `CURRICULA.md` from source IDs.

For an intentional error prediction, attach a successful `completion` scenario.
The emitter keeps the read ID and emits new `choose-repair-` and `write-repair-`
IDs. The reading card links to `repair_question_id`; a repair writing card has
`target_answer`, which is interpolated with its sampled parameters. These
optional fields are for traceability and developer validation; they never cause
the tutor to execute code. Preserve the original meaning of any retained ID.

`tests/fixtures/v1_course_ids.json` freezes the v1.0.0 question contracts and
lesson identities. Changed contracts should receive new IDs, not rewritten
history or silently repurposed prior successes. Native validation is optional:
`uv run python tools/verify_native_revision.py` runs trusted fixtures, reports
missing runtimes, and excludes undefined behavior and host-dependent examples.


## C/C++ whitespace matching (1.1.2)

Use `checker: "c_tokens"` for C/C++ code fragments. It compares lexical tokens
without executing submissions, ignoring whitespace between tokens while retaining
literal contents and compound operators. `x + 6` and `x+6` match, whereas `x++6`
and `x + +6`, or `"a b"` and `"ab"`, do not. This is a conservative fragment
checker, not a full C/C++ parser or semantic equivalence engine. Comments,
preprocessor directives, and line splices fall back to exact matching.

The builder assigns this checker to C/C++ writing cards, except command-line
and preprocessor fragments. Existing question IDs and stored history remain
unchanged: this intentionally broadens accepted formatting rather than changing
the target construction. The v1 compatibility regression allows only this
specific checker/prompt change; it still protects the original code and answers.
