# Six new language-native courses — 1.3.0

Each course has 20 lessons and 240 exercises: 6 Basics lessons, 7 Intermediate,
and 7 Advanced. Each lesson has four distinct scenarios, each developed through
prediction, guided completion, and a writing fragment. Read all eight MCQs
before the four writing tasks. Question IDs are stable; supported numeric and
text parameters change together with answers and explanations.

The full application now contains 17 courses, 344 lessons, and 4,152 exercises.
Existing banks, lesson completions, exam history, and review schedules are
unchanged. New course IDs have independent progress and support existing pins,
25-question section exams (>80% to pass), and spaced review automatically.

| Course ID | Baseline | Native learning emphasis |
| --- | --- | --- |
| `java` | Java 21+, no preview features | JDK/JVM, pass-by-value, interfaces, collection contracts, variance, checked exceptions, resource closure, records, streams, Optional, modules, virtual threads, futures |
| `go` | Go 1.22+ | Modules, zero values, byte/rune distinction, slices and aliasing, map absence, method sets, implicit interfaces, typed nil, wrapped errors, defer, generic constraints, channels, cancellation, tests |
| `csharp` | C# 12 / .NET 8+ | SDK projects, nullable contracts, ref/out, properties, value/reference semantics, interfaces, exception filters, using, records, delegates/events, LINQ, iterators, Tasks and cancellation |
| `bash` | Bash 5.2+, Unix-like host | Word/argument boundaries, quoting, exit status, expansion, globs, line reading, function scope, file descriptors, pipelines, subshells, arrays, patterns, environment, traps, wait/exec, safe command construction |
| `kotlin` | Kotlin 2.x / JVM | val versus object mutation, null safety, smart casts, read-only views, properties, data classes, static extension resolution, scope functions, sealed models, variance, lazy sequences, Java interop, suspension |
| `swift` | Swift 6 language mode | Unicode character semantics, labels/inout, optionals, guard, value semantics, properties, associated-value enums, class identity, protocols, capture lists, opaque/existential types, errors, ARC, async let, actors |

These tracks deliberately omit third-party frameworks and algorithm or
data-structure implementation lessons. Standard collection *usage* belongs in
the language courses. Kotlin's final lesson distinguishes the built-in suspend
contract and low-level standard-library continuations from the separate
kotlinx.coroutines library; it does not teach an Android or kotlinx track.
C# does not require Unity/ASP.NET, Swift does not require SwiftUI, and Go does
not require a web framework. Compilers are not needed to use the tutor.

## Curriculum sources

Sources guide topic selection and semantic checking. Exercises and teaching
prose are original; no source assignments or long passages are copied.

- Java: [official learning paths](https://dev.java/learn/), covering the language,
  JVM tooling, standard APIs, records, streams, and concurrency.
- Go: [official documentation](https://go.dev/doc/),
  [language specification](https://go.dev/ref/spec), and
  [Effective Go](https://go.dev/doc/effective_go). Effective Go alone predates
  newer features, so it is supplemented by the specification.
- C#: [Microsoft's language overview](https://learn.microsoft.com/en-us/dotnet/csharp/tour-of-csharp/overview)
  and [using/disposal reference](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/using).
- Bash: [GNU manual](https://www.gnu.org/software/bash/manual/) and the installed
  shell's builtin `help` for command contracts. The GNU web pages timed out
  during this revision; executable behavior was checked against local Bash.
- Kotlin: [basic syntax](https://kotlinlang.org/docs/basic-syntax.html),
  [Koans](https://kotlinlang.org/docs/koans.html),
  [extensions](https://kotlinlang.org/docs/extensions.html), and
  [coroutine overview](https://kotlinlang.org/docs/coroutines-overview.html).
- Swift: [The Swift Programming Language](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/)
  and its [ARC chapter source](https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/AutomaticReferenceCounting.md).
  The rendered book pages required JavaScript; ARC was readable from the
  official repository. Other Swift topic checks rely on language review and
  remain uncompiled here.

The generated [course map](CURRICULA.md) lists every lesson and its references.

## Validation and limits

- 92 automated tests pass. Existing language regression tests now include all
  six tracks: randomized cards, expected/wrong answer checks, complete lesson
  traversal, balanced 25-question section exams, and unlock behavior.
- Added regressions check Bash expansion syntax surviving template rendering,
  Java error-to-repair linkage, native topic coverage, and namespaced review
  alongside persistent language pins.
- `uv run python tools/verify_added.py` passes **146 Bash** and **132 Java**
  sampled programs across two seeds. Bash programs run in disposable empty
  directories with a controlled environment. The Java audit includes expected
  compiler rejection of final-variable reassignment.
- The installed Java 17 compiler module verifies the compatible subset; the
  Java 21 virtual-thread example is excluded. Go, .NET, Kotlin, and Swift
  compilers are unavailable. Their card/schema/integration checks pass, but
  these are not native compiler/runtime verification.
- Native audit does not execute every completion distractor or conceptual
  command description, and never compiles or runs learner submissions.
