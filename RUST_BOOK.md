# Rust: learn the language on its own terms

The Rust course follows [The Rust Programming Language](https://doc.rust-lang.org/book/)
and uses Rust 1.90+ / edition 2024. It contains **26 lessons, 312 exercises**:
8 Basics lessons, 9 Intermediate lessons, and 9 Advanced lessons. Every lesson
has 8 reading MCQs followed by 4 writing exercises. Each section exam contains
25 questions, includes reading and writing from every lesson, and requires more
than 80% (21/25) to pass. Exams cost no hearts.

The course emphasizes reading real Rust contracts: ownership at call boundaries,
receiver types, borrowed versus owned text, exhaustive domain states, Result
propagation, trait bounds, and safe concurrency. Cargo commands and manifest
snippets are labelled separately from Rust code. Examples use the standard
library and do not add framework or third-party async-runtime lessons.

Exercises and explanations are original. Chapter references support the topic
sequence and language rules; the book's full assignments are not reproduced.


| Section | Lesson | Book references |
| --- | --- | --- |
| Basics | Cargo, crates, and the edit-check cycle | [Rust Book chapter 1: Getting started and Cargo](https://doc.rust-lang.org/book/ch01-03-hello-cargo.html) |
| Basics | Immutability, mutability, and shadowing | [Rust Book chapter 3: Common programming concepts](https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html) |
| Basics | Types, expressions, and explicit conversion | [Rust Book chapter 3: Common programming concepts](https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html) |
| Basics | Functions and expression returns | [Rust Book chapter 3: Common programming concepts](https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html) |
| Basics | Boolean conditions and expressions | [Rust Book chapter 3: Common programming concepts](https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html) |
| Basics | Ranges and loop expressions | [Rust Book chapter 3: Common programming concepts](https://doc.rust-lang.org/book/ch03-00-common-programming-concepts.html) |
| Basics | Moves, Copy, and Drop | [Rust Book chapter 4: Ownership, references, and slices](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html) |
| Basics | References and lifetimes | [Rust Book chapter 4: Ownership, references, and slices](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html) |
| Intermediate | Strings, slices, and UTF-8 | [Rust Book chapter 4: Ownership, references, and slices](https://doc.rust-lang.org/book/ch04-00-understanding-ownership.html), [Rust Book chapter 8: Common collections](https://doc.rust-lang.org/book/ch08-00-common-collections.html) |
| Intermediate | Structs and enums as domain models | [Rust Book chapter 5: Structs and methods](https://doc.rust-lang.org/book/ch05-00-structs.html), [Rust Book chapter 6: Enums and pattern matching](https://doc.rust-lang.org/book/ch06-00-enums.html) |
| Intermediate | Destructuring, guards, and let-else | [Rust Book chapter 6: Enums and pattern matching](https://doc.rust-lang.org/book/ch06-00-enums.html), [Rust Book chapter 19: Patterns and matching](https://doc.rust-lang.org/book/ch19-00-patterns.html) |
| Intermediate | Modules, visibility, and imports | [Rust Book chapter 7: Packages, crates, and modules](https://doc.rust-lang.org/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html) |
| Intermediate | Tuples, arrays, and vectors | [Rust Book chapter 8: Common collections](https://doc.rust-lang.org/book/ch08-00-common-collections.html) |
| Intermediate | Option, Result, and propagation | [Rust Book chapter 9: Error handling](https://doc.rust-lang.org/book/ch09-00-error-handling.html) |
| Intermediate | Structs, methods, and traits | [Rust Book chapter 5: Structs and methods](https://doc.rust-lang.org/book/ch05-00-structs.html), [Rust Book chapter 10: Generics, traits, and lifetimes](https://doc.rust-lang.org/book/ch10-00-generics.html) |
| Intermediate | Generic APIs and trait bounds | [Rust Book chapter 10: Generics, traits, and lifetimes](https://doc.rust-lang.org/book/ch10-00-generics.html) |
| Intermediate | Borrowed APIs and lifetime relationships | [Rust Book chapter 10: Generics, traits, and lifetimes](https://doc.rust-lang.org/book/ch10-00-generics.html) |
| Advanced | Closures and lazy iterators | [Rust Book chapter 13: Closures and iterators](https://doc.rust-lang.org/book/ch13-00-functional-features.html) |
| Advanced | Unit tests, integration tests, and documentation | [Rust Book chapter 11: Automated tests](https://doc.rust-lang.org/book/ch11-00-testing.html) |
| Advanced | A useful CLI: arguments, files, errors, and exit status | [Rust Book chapter 12: A command-line I/O project](https://doc.rust-lang.org/book/ch12-00-an-io-project.html), [Rust Book chapter 9: Error handling](https://doc.rust-lang.org/book/ch09-00-error-handling.html) |
| Advanced | Cargo profiles, workspaces, and public docs | [Rust Book chapter 14: Cargo and crates.io](https://doc.rust-lang.org/book/ch14-00-more-about-cargo.html) |
| Advanced | Box, Rc, RefCell, and Weak | [Rust Book chapter 15: Smart pointers](https://doc.rust-lang.org/book/ch15-00-smart-pointers.html) |
| Advanced | Threads, channels, Arc, and Mutex | [Rust Book chapter 16: Fearless concurrency](https://doc.rust-lang.org/book/ch16-00-concurrency.html) |
| Advanced | Lazy futures, await, and cancellation | [Rust Book chapter 17: Async, await, futures, and streams](https://doc.rust-lang.org/book/ch17-00-async-await.html) |
| Advanced | Trait objects and API design | [Rust Book chapter 18: Object-oriented design and trait objects](https://doc.rust-lang.org/book/ch18-00-oop.html), [Rust Book chapter 20: Advanced Rust features](https://doc.rust-lang.org/book/ch20-00-advanced-features.html) |
| Advanced | Unsafe boundaries, newtypes, and macros | [Rust Book chapter 20: Advanced Rust features](https://doc.rust-lang.org/book/ch20-00-advanced-features.html) |

## How exercises develop fluency

Prediction cards ask for output, compiler rejection, a panic, an error result,
or an API contract. Numbers and text vary when that changes useful reasoning.
Follow-up cards ask the learner to select and then write a code fragment.
All ten intentionally invalid/panicking scenarios have separate repair follow-ups:
learners identify the problem first, then construct a valid alternative.

New families cover shadowing with a type change, checked arithmetic, UTF-8 bytes
versus scalar values, borrowing in patterns, HashMap entry updates, moving values
into containers, map_err, lifetime relationships, generic bounds, test attributes,
CLI arguments and exit status, workspace manifests, Rc/Weak and RefCell, channels,
Arc/Mutex, unpolled futures, dyn-compatible APIs, newtypes, and unsafe boundaries.

This is a set of focused reading/writing exercises. It teaches the contracts used
in larger projects without adding algorithm or data-structure implementation
lessons. The final book web-server/thread-pool project and external-runtime
examples are outside this course's current exercise scope.

## Existing progress

The course still uses the stable `rust` identity. Unchanged families retain their
IDs. Replaced families and genuinely new topics have new IDs; stored attempts
are retained, but retired families are excluded from the current review queue.
Retained completed lessons stay completed, including when their content is
expanded; replay them to practice the added cards. New and replacement lessons
start incomplete. Previous exam bonuses are not awarded again, although passing
an updated section exam marks all its current lessons done.

## Verification

The Python test suite samples 30 variants of every Rust card, completes every
lesson and all three exams, checks per-chapter references, verifies all ten repair
follow-ups, and exercises preservation of earlier progress. The full application
suite has 69 passing tests. Feedback title colors were also checked in a real PTY.

A native Rust compiler was unavailable in the build environment, so these Rust
snippets have **not been compiler-validated here**. The included optional audit
can independently compile/run their behavior on a machine with Rust 1.90+:

```bash
uv run python tools/verify_rust.py
```

It checks authored output predictions, expected compiler diagnostics, the
RefCell panic, test-harness behavior, CLI stderr/exit status, immediate future
completion, and repair fragments at two seeds. Command/manifests and execution
model explanations remain reference-reviewed. It uses temporary files, the
standard library, and no crate downloads; it never executes learner submissions.
