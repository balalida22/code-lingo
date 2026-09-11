# Language-native curriculum review — 1.1.0

The review covered all eleven courses. Python already teaches its own idioms
(aliasing, comprehensions, generators, context management, dataclasses,
decorators, and async), and Rust already follows the Rust Book. Their banks are
unchanged. The nine other tracks now have 20 lessons and 240 exercises each.
The whole application has 224 lessons and 2,688 exercises: 54 lessons and 648
exercises added in this revision.

Depth means useful language coverage, not identical topic lists. The courses
share basic ideas where those ideas really transfer, but their intermediate
and advanced pathways follow the language's own contracts and common uses.
Each lesson still has four scenarios, scaffolded into eight reading/completion
MCQs and four writing cards. These are twelve exercises, not twelve independent
concepts. Constants such as INT_MAX, NULL, or a leap-day boundary intentionally
remain fixed; incidental values and words are randomized when useful.

| Course | Audit finding and resulting focus | Main references |
| --- | --- | --- |
| C | Add compilation/linking, integer conversions, buffer capacity, storage duration, masks, and CLI boundaries; teach pointers before allocation | [CS50 C](https://cs50.harvard.edu/x/weeks/1/), [GCC stages](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html), [C17 draft](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n2176.pdf) |
| C++ | Add initialization, copy versus move, rule of zero, borrowed span/string_view, variants/concepts, and synchronized threads after ownership | [Learn C++](https://www.learncpp.com/), [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) |
| TypeScript | Separate static checking from runtime behavior; add structural compatibility, unknown validation, key-dependent APIs, compiler flags, literal contracts, and promise boundaries | [Handbook](https://www.typescriptlang.org/docs/handbook/intro.html), [Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html), [TSConfig](https://www.typescriptlang.org/tsconfig/) |
| Vanilla web | Add semantic/keyboard behavior, Grid and sizing constraints, JavaScript identity/receivers, microtasks, form serialization, origins/storage/lifecycle | [MDN core](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core), [JavaScript guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide) |
| Ruby | Add script conventions, Ruby 3 keyword arguments, structural patterns, regex/bang return contracts, Enumerable protocols, and tests/JSON boundaries | [Ruby quickstart](https://www.ruby-lang.org/en/documentation/quickstart/), [Ruby syntax](https://docs.ruby-lang.org/en/3.3/syntax_rdoc.html) |
| Lua | Add chunks and environments, multiple-result adjustment, nil holes, iterator protocols, patterns/UTF-8, to-be-closed locals, module caching, and host boundaries | [Lua 5.4 manual](https://www.lua.org/manual/5.4/manual.html) |
| PHP | Add request lifetimes, input shape checks, context-specific output encoding, HTTP responses, JSON failures, PDO parameters/transactions, and modern value contracts | [PHP manual](https://www.php.net/manual/en/), [PDO parameters](https://www.php.net/manual/en/pdo.prepared-statements.php) |
| Perl | Add one-liners, text pipelines, literal regex matching, lexical versus dynamic scope, file/encoding/process boundaries, and core Test::More; teach context before pipelines | [Perl introduction](https://perldoc.perl.org/perlintro), [Invocation](https://perldoc.perl.org/perlrun), [Regex tutorial](https://perldoc.perl.org/perlretut) |
| SQL | Add three-valued logic, SQLite affinity, ON versus WHERE in outer joins, window frames, date/compound-query semantics, and transactional schema changes | [CS50 SQL](https://cs50.harvard.edu/sql/), [SQLite types](https://www.sqlite.org/datatype3.html), [SELECT](https://www.sqlite.org/lang_select.html), [Window functions](https://www.sqlite.org/windowfunctions.html) |

The new lessons use standard language/platform facilities. PDO requires an
installed database driver, and Ruby's Test::Unit may require its gem; examples
state these assumptions. There are no new framework/library-specialization
tracks and no algorithm or data-structure implementation lessons. SQL remains
explicitly a SQLite 3.35+ course rather than implying all SQL dialects agree.

## Diagnosis before repair

An error prediction keeps its original read ID where its meaning is unchanged.
The subsequent completion and writing cards have `repair-` IDs and require a
successful correction. Examples include an out-of-bounds C access, copying a
unique_ptr, missing Ruby keywords, changing a Lua const local, a PHP strict-type
failure, a TypeScript unknown value, a JavaScript temporal dead zone, and SQL
constraint violations. Intentional undefined behavior is never native-executed.

Repair cards include a `target_answer` for developer verification, and the
diagnosis points to its `repair_question_id`. Both are declarative metadata;
the application never runs code. Existing history is not reinterpreted as a
new answer to a changed exercise.

## Existing profiles

- All 14 old lesson IDs in each expanded course remain present and keep their
  completion state. Six added lessons per course start unfinished.
- Retained question IDs keep the same code, answers, variants, and checking
  contracts. Superseded completion IDs remain stored but are omitted from
  current review pools. New repair IDs start unattempted.
- XP, gems, hearts, streaks, attempts, mistakes, and exam records remain stored.
  A resumed unfinished lesson reuses history for its retained questions.
- Prerequisite order and some section memberships now follow native concepts.
  Existing completion is respected. Old section passes do not automatically
  complete added topics; study them or retake the current section exam.
- Exams still have 25 questions, require 21 correct to pass, cost no hearts,
  and mark every lesson in the selected section complete on a passing finish.

`tests/fixtures/v1_course_ids.json` records the old identities and fingerprints
from the local v1.0.0 tag. Regression tests protect retained meanings, old
history, new unfinished topics, resumption, and section-exam behavior.

## Verification scope

73 automated tests pass, including course loading, randomized variants, all
lesson/exam paths, identity/history checks, and the existing gameplay/UI suite.
SQLite's 80 reading scenarios are executed at three seeds by the regression
suite, including expected constraint failures.

The optional developer audit additionally passed 870 sampled output predictions
and repaired programs (two seeds each): C 118, C++ 140, Lua 152, Perl 130,
JavaScript 52, TypeScript 140, SQLite 138. Twelve expected TypeScript type
failures also passed with TypeScript 5.6.3, including compiler-option-specific
cases. This is a count of sampled programs, not unique
exercise families or exhaustive coverage. The C null-terminator regression
found during preparation was corrected and the C audit repeated successfully.

Ruby and PHP executables and a browser runtime were unavailable.
Their content has schema/variant and reference-based review, not claimed native
execution. C/C++ undefined behavior, conceptual/compiler-diagnostic cards,
shell commands, and host-dependent snippets are excluded from the output audit.
Python and Rust retain their prior validation scope. Exact-fragment checks do
not accept every semantically equivalent solution.

```bash
uv run python -m unittest discover -s tests -v
uv run python tools/verify_native_revision.py
# TypeScript output and deliberate compiler failures (requires tsc and Node):
uv run python tools/verify_typescript.py
# Recheck just the installed runtimes you want:
uv run python tools/verify_native_revision.py --courses c cpp lua perl web sql
```

The native audit uses only trusted authored fixtures in temporary directories.
Lua can use an installed 5.4 shared library if its CLI is absent. These tools
are never called from the learning application.
