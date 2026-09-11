# Expanded Python library learning — v1.4.0

Select **Change language / library** and choose one of the **Python ·** library
tracks. Each library now has 12 progressive lessons and 144 exercises, in
addition to its unchanged 12-question sampler in the original Python course.
Each lesson teaches four distinct scenarios through prediction, completion,
and writing. Parameterized examples resample their values on later encounters.

| Track | Foundations (4 lessons) | Workflows (4 lessons) | Advanced usage (4 lessons) |
| --- | --- | --- | --- |
| NumPy | Arrays and metadata; creation; indexing; elementwise operations | Reductions and axes; broadcasting; copies/views; masks | Reshape/transpose/join; dtypes and NaN; generators; numerical workflows and persistence |
| Matplotlib | Figure/Axes/artists; lines; scatter; labels and legends | Panel grids; limits/scales/ticks; bars/histograms; images/colorbars | Coordinate transforms; scoped styles; artist updates; export and structural tests |
| PyTorch | Tensor metadata; shapes/layout; batch-preserving indexing; broadcasting/reductions | Autograd; detach/clone/storage; modules; eval versus gradient contexts | Datasets/loaders; training-step order; device/dtype boundaries; state dictionaries/checkpoints |
| Transformers | Assets and task heads; tokenization; padding/truncation; batch dictionaries | Task-dependent outputs; inference mode; generation budgets; continuation decoding | Chat templates; labels/collators; asset persistence/revisions; integration debugging |

All tracks assume Python functions, collections, and imports. They are
independently selectable and pinnable, without requiring completion of the
entire Python course. Each section contains four lessons and its own balanced
25-question exam: passing requires 21 correct answers, costs no hearts, and
marks that section's lessons done. Lessons and exams count toward the existing
daily goal; learned questions enter the existing spaced-review schedule.

The new content adds **48 lessons and 576 exercises**, bringing the application
to **21 courses, 392 lessons, and 4,728 exercises**. These are API-reading and
workflow courses, not courses in implementing algorithms or data structures.
PyTorch loss/gradient examples explain library calls and state changes rather
than deriving machine-learning methods.

## Progress compatibility

The original `python` bank and the other 16 existing banks remain byte-identical.
Your sampler completions, attempts, review schedules, EXP, hearts, and pins
retain their meaning. New library-track progress starts separately: completing
one old sampler does not award mastery of twelve new lessons. Sampler teaching
pages point to the expanded track. No database schema migration is needed.

## Question behavior

- Values, shapes where appropriate, and string literals are parameterized.
  Answers and explanations use the same sampled values.
- Exact model token IDs or generated text are not guessed. Transformers
  questions either specify concrete fixtures or ask about the API contract.
  Pure Python dictionary/stub examples are explicitly identified.
- NumPy's incompatible-broadcast example leads into a repair that inserts the
  correct singleton axis.
- Library writing questions compare the Python syntax of the completed snippet.
  Equivalent spaces and quote styles work, including slices and keyword
  arguments. Different literal contents or AST structure still count as different
  answers. The tutor never runs learner submissions.
- Using the tutor requires neither these libraries nor model weights, network
  access, a GPU, or a plotting window.

## References and baselines

Exercises and prose are newly authored; official material guides topic order
and API semantics rather than being reproduced verbatim.

- **NumPy 2.x:** [beginner guide](https://numpy.org/doc/stable/user/absolute_beginners.html),
  [broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html),
  [copies and views](https://numpy.org/doc/stable/user/basics.copies.html).
- **Matplotlib 3.8+:** [quick start](https://matplotlib.org/stable/users/explain/quick_start.html)
  and [Axes API](https://matplotlib.org/stable/api/axes_api.html).
- **PyTorch 2.x:** [beginner tutorials](https://docs.pytorch.org/tutorials/beginner/basics/intro.html),
  [autograd notes](https://docs.pytorch.org/docs/stable/notes/autograd.html),
  [serialization notes](https://docs.pytorch.org/docs/stable/notes/serialization.html).
- **Transformers 4.57 API family, PyTorch backend:**
  [quick tour](https://huggingface.co/docs/transformers/v4.57.1/quicktour),
  [padding/truncation](https://huggingface.co/docs/transformers/v4.57.1/pad_truncation),
  [generation](https://huggingface.co/docs/transformers/v4.57.1/main_classes/text_generation),
  [chat templates](https://huggingface.co/docs/transformers/v4.57.1/chat_templating).
  This baseline is explicit; the course does not claim full compatibility with
  later major versions. The pinned padding page was unavailable during browsing;
  the quick tour and API contract review informed those examples.

See [CURRICULA.md](CURRICULA.md) for the generated per-lesson map.

## Validation

**97 tests pass**, including 20 rendered variants of each new template, accepted
and rejected answer checks, context-sensitive fragment grading, complete lesson
traversal, review enrollment, and all twelve section exams. Tests also confirm
that old sampler completions do not fabricate new-track progress.

The optional `python tools/verify_python_libraries.py` audit executes only trusted
authored examples using a separate installed-library interpreter. It passed
**291 NumPy/Matplotlib output and repair variants** over three seeds using
NumPy 2.3.5 and Matplotlib 3.10.8. Matplotlib uses the noninteractive Agg backend;
figures are closed, and file operations use temporary directories. The audit
includes the expected incompatible-broadcast ValueError.

PyTorch and Transformers are unavailable in this environment. Their schema,
syntax, grading, and lesson/exam integration tests pass, but their snippets have
not been executed against those libraries here. Native audit results do not
cover every distractor, arbitrary hardware behavior, or downloaded model behavior.
