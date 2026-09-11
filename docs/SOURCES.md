# Curriculum sources and reuse

Sources reviewed on 9 September 2026. This prototype uses open teaching
materials to select topics and a sensible sequence, then supplies original
short examples, MCQs, distractors, hints, and writing prompts. It does not bundle
scraped courses, copied exercise banks, model weights, or third-party packages.

| Source | Why it was selected | Used in Code Lingo |
| --- | --- | --- |
| [University of Helsinki, Python Programming MOOC 2026](https://programming-26.mooc.fi/part-1/1-getting-started/) | University beginner course with a concrete progression through output, input, variables, arithmetic, and conditionals | Early topic ordering; original examples and questions |
| [The Carpentries, Plotting and Programming in Python](https://swcarpentry.github.io/python-novice-gapminder/) | Open practical workshop curriculum covering names, conversion, functions, libraries, plotting, loops, and scope | Practical framing and topic progression; adapted into much shorter reading checks |
| [Python Software Foundation, Python Tutorial](https://docs.python.org/3/tutorial/) | Primary reference for Python language features | Syntax/semantics coverage for Intermediate and Advanced; original exercises |
| [NumPy, Absolute basics for beginners](https://numpy.org/doc/stable/user/absolute_beginners.html) | Official introduction to arrays, dimensions, indexing, and operations | NumPy sampler: shape, broadcasting, axes, and views |
| [Matplotlib, Quick start guide](https://matplotlib.org/stable/users/explain/quick_start.html) | Official introduction to figures and Axes | Matplotlib sampler: explicit plotting calls and labels |
| [PyTorch, Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html) | Official staged introduction to the library | PyTorch sampler: tensors and inference idioms, with training algorithms omitted |
| [Hugging Face, LLM Course: Behind the pipeline](https://huggingface.co/learn/llm-course/en/chapter2/2) | Open course explaining tokenization and model invocation | Transformers sampler: input mapping, batching, calls, and output interpretation |

Additional primary reference consulted: [Matplotlib's pyplot tutorial](https://matplotlib.org/stable/tutorials/pyplot.html).

## Attribution and changes

The curriculum draws on the topic progression of **The Carpentries, Plotting
and Programming in Python**, copyright The Carpentries and its contributors.
Its instructional material is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
and its example software under MIT, as stated on the course's
[license page](https://swcarpentry.github.io/python-novice-gapminder/LICENSE.html).
Changes here include reordered topics, omitted data analysis and algorithm
material, entirely new examples and questions, and a reading-first interactive
format. The Carpentries does not endorse this project.

Helsinki and the other documentation/course sources are used as references,
not as copied text or example-code collections. No assertion is made here that
every freely readable page has the same reuse license. If importing substantial
material in a later version, inspect that source's current content license,
retain notices, identify adaptations, and record provenance per lesson/card.

The generated Code Lingo course text and exercise bank are offered under
**Creative Commons Attribution 4.0 International**. Attribute “Code Lingo course
contributors” and retain the source acknowledgments above when redistributing
adaptations. The CLI software's MIT license is in `LICENSE`.

Every lesson declares its source IDs in the JSON course. `python3 -m codelingo
sources` exposes these references from the CLI. Specialized material is an
introductory API sampler; it intentionally omits the mathematical or algorithmic
curriculum from the full upstream courses.

## Version 0.2 additions

The expanded exercise bank contains 216 authored problems, including 126 CLQ
parameterized templates. The source-course mapping above still applies. New
content focuses on varying literals, arguments, and contexts while retaining
consistent code and answers. No additional upstream exercise bank was copied.

Implementation references: [uv project locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
and [Python's curses HOWTO](https://docs.python.org/3/howto/curses.html).

## Additional language references

The ten added curricula use the following open courses and official references for topic ordering and language rules. All new scenarios, explanations, and questions are original; no source exercise banks are redistributed.

| Course | Reference |
| --- | --- |
| C | [CS50x C lectures](https://cs50.harvard.edu/x/weeks/1/) |
| C | [GNU C language manual (portable C subset here)](https://www.gnu.org/software/c-intro-and-ref/manual/html_node/) |
| C++ | [Learn C++](https://www.learncpp.com/) |
| Lua | [Lua 5.4 Reference Manual](https://www.lua.org/manual/5.4/) |
| PHP | [PHP language reference](https://www.php.net/manual/en/langref.php) |
| Perl | [Perl introduction and tutorials](https://perldoc.perl.org/perlintro) |
| Perl | [Perl reference tutorial](https://perldoc.perl.org/perlreftut) |
| Ruby | [Ruby in Twenty Minutes](https://www.ruby-lang.org/en/documentation/quickstart/) |
| Ruby | [Ruby syntax reference](https://docs.ruby-lang.org/en/master/syntax_rdoc.html) |
| Rust | [The Rust Programming Language](https://doc.rust-lang.org/book/) |
| Rust | [Rust Reference](https://doc.rust-lang.org/reference/) |
| SQL (SQLite) | [CS50 Introduction to Databases with SQL](https://cs50.harvard.edu/sql/) |
| SQL (SQLite) | [SQLite SQL language reference](https://www.sqlite.org/lang.html) |
| TypeScript | [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html) |
| Vanilla HTML + CSS + JavaScript | [MDN core learning modules](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core) |
| Vanilla HTML + CSS + JavaScript | [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide) |

## Rust Book-led revision (0.3.1)

Rust now has a dedicated authoring module and chapter-specific references in
all 26 lessons. [RUST_BOOK.md](RUST_BOOK.md) maps those lessons to the book.
Ownership and borrowing are introduced before owned collection APIs; additional
material covers tests, Cargo workspaces, CLI design, smart pointers, concurrency,
async semantics, trait objects, and advanced language boundaries. The revised
examples and repair exercises are newly authored; no book project is bundled.

## Native curriculum revision (1.1.0)

[NATIVE_CURRICULA.md](NATIVE_CURRICULA.md) explains the review and its primary
references. [CURRICULA.md](CURRICULA.md) provides per-lesson links emitted from
the source IDs. New material is authored for Code Lingo; no upstream prose,
assignments, or exercise banks are bundled. Python and Rust sources are unchanged.

The C17 committee draft is listed as a language reference; its PDF could not be
parsed by the research reader in this session. C execution checks and the
accessible GCC/CS50 references supplement the editorial review. Reference
availability and runtime validation are separate from the course answer checks.

## Six added tracks (1.3.0)

Java, Go, C#, Bash, Kotlin, and Swift follow official language learning and
reference material. See [NEW_LANGUAGES.md](NEW_LANGUAGES.md) for exact sources,
baselines, native topic choices, and which reference pages or runtimes were
unavailable during validation. All exercises and explanations are newly authored.
The machine-readable banks include source IDs; [CURRICULA.md](CURRICULA.md)
provides the complete per-lesson map.


## Python library expansion (1.4.0)

The dedicated NumPy, Matplotlib, PyTorch, and Transformers courses use official
API guides listed in [PYTHON_LIBRARIES.md](PYTHON_LIBRARIES.md). The Transformers
course explicitly targets the documented 4.57 API family instead of silently
following breaking major-version changes. Exact token IDs, model output values,
and generated text are never inferred from an unspecified checkpoint.
All examples and explanations are original, and source pages are references
rather than copied course assignments.
