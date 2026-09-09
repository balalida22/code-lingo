"""CLQ templates: sampled parameters, bounded expressions, and interpolation.

No eval/exec, imports, attributes, comprehensions, or user-defined calls.
Displayed code is never executed. Parameters and derived values are data.
"""
import ast
import copy
import operator
import random
import re

TOKEN = re.compile(r"\$\{([a-zA-Z_][a-zA-Z_0-9]*)\}")
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
FUNCS = {"str": str, "repr": repr, "len": len, "sum": sum, "abs": abs,
         "min": min, "max": max, "round": round,
         "upper": lambda s: s.upper(), "lower": lambda s: s.lower(),
         "strip": lambda s: s.strip()}


def expression(source, values):
    if len(source) > 1000:
        raise ValueError("Template expression too long")
    tree = ast.parse(source, mode="eval")
    if sum(1 for _ in ast.walk(tree)) > 100:
        raise ValueError("Template expression too complex")

    def bounded(value):
        if isinstance(value, (str, list, tuple, dict)) and len(value) > 2000:
            raise ValueError("Template value too large")
        if isinstance(value, (int, float)) and abs(value) > 1000000:
            raise ValueError("Template number too large")
        return value

    def visit(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool, type(None))):
            value = node.value
        elif isinstance(node, ast.Name) and node.id in values:
            value = values[node.id]
        elif isinstance(node, (ast.List, ast.Tuple)):
            items = [visit(x) for x in node.elts]
            value = tuple(items) if isinstance(node, ast.Tuple) else items
        elif isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Mult):
                seq, n = (left, right) if isinstance(right, int) else (right, left)
                if isinstance(seq, (str, list, tuple)) and isinstance(n, int) and len(seq) * n > 2000:
                    raise ValueError("Template repetition too large")
            value = OPS[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand) * (-1 if isinstance(node.op, ast.USub) else 1)
        elif isinstance(node, ast.Subscript):
            value = visit(node.value)[visit(node.slice)]
        elif isinstance(node, ast.Slice):
            return slice(*(visit(x) if x is not None else None for x in (node.lower, node.upper, node.step)))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
            value = FUNCS[node.func.id](*(visit(a) for a in node.args))
        else:
            raise ValueError("Disallowed template expression: " + ast.dump(node))
        return bounded(value)
    return visit(tree.body)


def render(question, rng=None):
    rng = rng or random.Random()
    if not question.get("parameters"):
        return copy.deepcopy(question)
    # Retry collisions caused by unlucky parameter combinations.
    for _ in range(100):
        values = {}
        for name, spec in question["parameters"].items():
            if not name.isidentifier():
                raise ValueError("Invalid parameter name")
            if spec.get("type") == "int":
                lo, hi = spec["min"], spec["max"]
                if not isinstance(lo, int) or not isinstance(hi, int) or not -10000 <= lo <= hi <= 10000:
                    raise ValueError("Invalid integer parameter range")
                values[name] = rng.randint(lo, hi)
            elif spec.get("type") == "choice" and spec.get("values"):
                values[name] = rng.choice(spec["values"])
            else:
                raise ValueError("Invalid parameter sampler")
        for name, formula in question.get("derived", {}).items():
            values[name] = expression(formula, values)

        def fill(value):
            if isinstance(value, str):
                return TOKEN.sub(lambda m: str(values[m.group(1)]), value)
            if isinstance(value, list):
                return [fill(x) for x in value]
            return value

        result = {k: fill(v) for k, v in question.items() if k not in {"parameters", "derived"}}
        if result["kind"] == "mcq":
            if len(set(result["options"])) != len(result["options"]):
                continue
            if result["answer"] not in result["options"]:
                raise ValueError("Rendered answer missing from options")
        result["variant"] = values
        return result
    raise ValueError("Could not generate distinct choices: " + question["id"])
