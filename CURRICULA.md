# Course curricula

Every lesson contains 12 exercises and each section has a 25-question exam. Rust has 26 lessons organized around the Rust Book. The other nine added languages have 14 lessons each, and Python retains its 18 lessons including specialized tracks.


## Python: read first, write next

Python

| Section | Lessons in order |
| --- | --- |
| Basics | Names, values, and output → Read expressions precisely → Input, types, and conversion → Strings, slices, and formatting → Branches and truthiness |
| Intermediate | Read everyday collection syntax → Follow loops in real scripts → Read function contracts and calls → Imports and module boundaries → Exceptions and resource cleanup |
| Advanced | Aliasing and Python gotchas → Objects, attributes, and dataclasses → Comprehensions and lazy iteration → Wrappers and asynchronous calls |
| Specialized | NumPy: shapes, axes, and broadcasting → Matplotlib: read a plotting script → PyTorch: tensors and inference idioms → Transformers: tokenizer-to-model flow |

## C

C17; standard headers such as stdio.h, stdlib.h, string.h, and limits.h are assumed where used

| Section | Lessons in order |
| --- | --- |
| Basics | Values and assignment → Arithmetic and precedence → Characters and C strings → Conditions and boolean operators → Loop bounds and control flow |
| Intermediate | Functions and value parameters → Arrays, sizes, and bounds → Formatted I/O and return values → Headers, linkage, and macros → Failure reporting and cleanup |
| Advanced | Pointers, const, and lifetime → Structures, enums, and typedef → Dynamic memory and ownership → Function pointers and low-level qualifiers |

## C++

C++20; relevant standard headers and a main function are assumed

| Section | Lessons in order |
| --- | --- |
| Basics | Values and assignment → Arithmetic and precedence → Strings and value types → Comparisons and scoped branches → Loops and range iteration |
| Intermediate | Parameters, overloads, and defaults → Standard containers and checked access → Streams and input state → Namespaces and type deduction → Exceptions and unwinding |
| Advanced | Classes and encapsulation → RAII and smart pointers → Templates and callable objects → Virtual dispatch and optional values |

## Lua

Lua 5.4

| Section | Lessons in order |
| --- | --- |
| Basics | Values and assignment → Arithmetic and precedence → Strings and coercion → Truthiness and expressions → Numeric and generic loops |
| Intermediate | Functions and multiple returns → Tables and absent values → Input, files, and conversion → Local scope and modules → Protected calls and assertions |
| Advanced | References and table mutation → Metatables and fallback lookup → Colon methods and closures → Coroutines and suspended execution |

## PHP

PHP 8.2+; snippets are inside a PHP block

| Section | Lessons in order |
| --- | --- |
| Basics | Values and assignment → Arithmetic and precedence → Strings and interpolation → Comparison and truthiness → Loops and foreach |
| Intermediate | Functions and typed parameters → Arrays and keys → Request values and basic I/O → Namespaces and loading → Exceptions and cleanup |
| Advanced | Classes and instance state → Interfaces, traits, and enums → Closures and capture → Generators and reference pitfalls |

## Perl

Perl 5; strict and warnings enabled; snippets omit those declarations

| Section | Lessons in order |
| --- | --- |
| Basics | Values and assignment → Arithmetic and precedence → Strings, sigils, and interpolation → Numeric and string comparison → Loops and loop controls |
| Intermediate | Subroutines and arguments → Arrays, hashes, and sigils → Handles, lines, and conversion → Packages and lexical declarations → die, eval, and error state |
| Advanced | References and dereferencing → Scalar and list context → Regular expressions and captures → Objects, methods, and closures |

## Ruby

Ruby 3.x

| Section | Lessons in order |
| --- | --- |
| Basics | Values and assignment → Arithmetic and precedence → Strings and symbols → Truthiness and branches → Iteration and ranges |
| Intermediate | Methods and arguments → Arrays and hashes → Input, output, and conversion → Modules and loading → Exceptions and cleanup |
| Advanced | Objects and encapsulation → Blocks, yield, and closures → Enumerable and lazy iteration → Aliasing, freezing, and method lookup |

## Rust: ownership, systems, and useful tools

Rust 1.90+ / edition 2024; standard library only. Rust snippets may omit main; commands and file names are labelled separately

| Section | Lessons in order |
| --- | --- |
| Basics | Cargo, crates, and the edit-check cycle → Immutability, mutability, and shadowing → Types, expressions, and explicit conversion → Functions and expression returns → Boolean conditions and expressions → Ranges and loop expressions → Moves, Copy, and Drop → References and lifetimes |
| Intermediate | Strings, slices, and UTF-8 → Structs and enums as domain models → Destructuring, guards, and let-else → Modules, visibility, and imports → Tuples, arrays, and vectors → Option, Result, and propagation → Structs, methods, and traits → Generic APIs and trait bounds → Borrowed APIs and lifetime relationships |
| Advanced | Closures and lazy iterators → Unit tests, integration tests, and documentation → A useful CLI: arguments, files, errors, and exit status → Cargo profiles, workspaces, and public docs → Box, Rc, RefCell, and Weak → Threads, channels, Arc, and Mutex → Lazy futures, await, and cancellation → Trait objects and API design → Unsafe boundaries, newtypes, and macros |

## SQL (SQLite)

SQLite 3.35+; every question starts with a fresh in-memory database; result order is specified when relevant

| Section | Lessons in order |
| --- | --- |
| Basics | SELECT expressions and aliases → Arithmetic, text, and NULL → Filtering with WHERE → Ordering and limiting results → Tables, types, and constraints |
| Intermediate | INSERT, UPDATE, and DELETE → Aggregates and grouping → Keys and joins → Subqueries and EXISTS → Views and common table expressions |
| Advanced | Transactions and savepoints → Uniqueness, foreign keys, and conflict handling → Window functions and analytic reading → Parameters, triggers, and NULL pitfalls |

## TypeScript

TypeScript with strict checking; ES2022 JavaScript target; runtime output assumes successful type-checking unless the question explicitly asks otherwise

| Section | Lessons in order |
| --- | --- |
| Basics | Bindings and primitive types → Numbers and string expressions → Branches and narrowing → Loops and iteration → Functions and parameter contracts |
| Intermediate | Object types and interfaces → Arrays, tuples, and destructuring → Modules and type-only imports → Unknown errors and safe handling → Classes and access control |
| Advanced | Generics and constraints → Discriminated unions and exhaustiveness → Mapped types and type operators → Promises, async, and type erasure |

## Vanilla HTML + CSS + JavaScript

Modern standards-mode browser; scripts execute after their referenced elements exist unless timing is the topic; await snippets are inside async functions

| Section | Lessons in order |
| --- | --- |
| Basics | HTML structure and semantics → Forms and accessible controls → Selectors and the cascade → Box model and flex layout → JavaScript values and branches |
| Intermediate | Functions, scope, and loops → DOM selection and safe text updates → Events and default actions → Objects, arrays, and JSON → Responsive CSS and states |
| Advanced | Promises and async execution → Fetch and response handling → Modules and closure state → DOM lifecycle and browser boundaries |
