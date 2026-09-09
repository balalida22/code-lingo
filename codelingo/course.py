"""Declarative course loading and non-executing answer checks."""

import ast
import json
import random
from pathlib import Path
from .templates import render
from .c_tokens import equivalent as c_equivalent


def syntax_tree(text):
    if len(text) > 2000:
        raise ValueError("Answer is too long")
    return ast.dump(ast.parse(text.strip()), include_attributes=False)


def check_answer(question, answer):
    """MCQs use their option text internally; Python writing uses AST matching.

    This deliberately checks listed constructions, not arbitrary semantic
    equivalence. Neither learner answers nor course snippets are executed.
    """
    if question["kind"] == "mcq":
        return answer == question["answer"]
    if question.get("checker", "python_ast") == "exact":
        return answer.strip() in question["accepted"]
    if question.get('checker')=='c_tokens':
        return any(c_equivalent(answer,a) for a in question['accepted'])
    try:
        submitted = syntax_tree(answer)
        return any(submitted == syntax_tree(a) for a in question["accepted"])
    except (SyntaxError, ValueError, RecursionError):
        return False


class Course:
    def __init__(self, data):
        self.data = data
        self.validate()
        self.id = data["id"]
        self.title = data["title"]
        self.lessons = data["lessons"]
        self.questions = {q["id"]: q for l in self.lessons for q in l["questions"]}
        self.by_id = {l["id"]: l for l in self.lessons}
        self.lesson_for = {q["id"]: l for l in self.lessons for q in l["questions"]}

    def validate(self):
        def require(condition, message):
            if not condition:
                raise ValueError("Invalid course: " + message)

        d = self.data
        require(d.get("schema_version") in {1, 2}, "schema_version must be 1 or 2")
        require(bool(d.get("id")) and bool(d.get("title")), "id/title required")
        require(bool(d.get("lessons")), "no lessons")
        sources = {s["id"] for s in d.get("sources", [])}
        seen, questions = set(), set()
        for lesson in d["lessons"]:
            lid = lesson["id"]
            require(lid not in seen, "duplicate lesson " + lid)
            require(set(lesson.get("requires", [])) <= seen,
                    "prerequisites must exist earlier: " + lid)
            seen.add(lid)
            require(lesson.get("section") in {"Basics", "Intermediate", "Advanced", "Specialized"}, "section")
            require(bool(lesson.get("intro")), "lesson needs teaching notes")
            require(bool(lesson.get("questions")), "empty lesson")
            require(bool(lesson.get("sources")) and set(lesson["sources"]) <= sources, "unknown source")
            writing = False
            for q in lesson["questions"]:
                # Validate concrete variants, not unresolved placeholders.
                if q.get("parameters"):
                    for seed in range(10):
                        sample = render(q, random.Random(seed))
                        if sample["kind"] == "write" and sample.get("checker", "python_ast") == "python_ast":
                            for a in sample["accepted"]:
                                syntax_tree(a)
                    q = render(q, random.Random(0))
                require(q["id"] not in questions, "duplicate question " + q["id"])
                questions.add(q["id"])
                require(q.get("kind") in {"mcq", "write"}, "question kind")
                require(all(q.get(k) for k in ("prompt", "explanation", "hint", "concept")), "question fields")
                require(not writing or q["kind"] == "write", "reading must precede writing")
                if q["kind"] == "mcq":
                    opts = q.get("options", [])
                    require(2 <= len(opts) <= 6 and len(set(opts)) == len(opts), "options must be distinct")
                    require(q.get("answer") in opts, "answer not in options")
                else:
                    writing = True
                    require(bool(q.get("accepted")), "missing accepted answers")
                    require(q.get("checker", "python_ast") in {"python_ast", "exact", "c_tokens"}, "checker")
                    if q.get("checker", "python_ast") == "python_ast":
                        for a in q["accepted"]:
                            syntax_tree(a)

    def key(self, question_id):
        return self.id + ":" + question_id

    def lesson_key(self, lesson_id):
        return self.id + ":" + lesson_id


def load_course(name="python", path=None):
    path = Path(path) if path else Path(__file__).parent / "courses" / (name + ".json")
    return Course(json.loads(path.read_text(encoding="utf-8")))


def course_catalog():
    """Metadata only; validate a full course when it is selected."""
    entries = []
    for path in sorted((Path(__file__).parent / "courses").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        entries.append({"id": path.stem, "title": data["title"],
                        "lessons": len(data["lessons"]),
                        "lesson_ids": [l["id"] for l in data["lessons"]],
                        "questions": sum(len(l["questions"]) for l in data["lessons"])})
    return sorted(entries, key=lambda c: (c["id"] != "python", c["title"]))
