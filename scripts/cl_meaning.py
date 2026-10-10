#!/usr/bin/env python3
"""Check every "rebuilt from the core" line in spec/cl-meaning.json against Common Logic's own rules.

The official rules below implement the cited draft's Table 1 rows (E8-E14) literally. A rebuild is
evaluated using only the official rules of the core pieces (not, and, for every), then compared
with the official rule of the class it rebuilds:
  - connectives: every true/false assignment, for each component count the class allows;
  - quantifiers: every world of 1-3 things and every choice of which things the body holds for.
    That is a check on small worlds, not a proof for all worlds, and the output says so.
Writes generated/cl-meaning-checks.json and prints one line per class.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "spec" / "cl-meaning.json"
DEFAULT_OUTPUT = ROOT / "generated" / "cl-meaning-checks.json"
WORLD_SIZES = (1, 2, 3)

# Table 1, read literally. Components are a list of truth values.
OFFICIAL_CONNECTIVES = {
    "Negation": lambda cs: cs[0] is False,                                   # E8
    "Conjunction": lambda cs: all(c is True for c in cs),                    # E9
    "Disjunction": lambda cs: not all(c is False for c in cs),              # E10
    "Implication": lambda cs: not (cs[0] is True and cs[1] is False),       # E11
    "Biconditional": lambda cs: cs[0] == cs[1],                              # E12
}
# A world: the things in the universe of discourse, and the set of things the body is true of.
OFFICIAL_QUANTIFIERS = {
    "UniversalQuantification": lambda things, holds: all(x in holds for x in things),          # E13
    "ExistentialQuantification": lambda things, holds: not all(x not in holds for x in things),  # E14
}
CORE_OPS = {"not", "and", "and_each", "forall"}


def ops_used(expr) -> set[str]:
    if isinstance(expr, str):
        return set()
    found = {expr["op"]}
    for key in ("arg", "each", "body"):
        if key in expr:
            found |= ops_used(expr[key])
    for a in expr.get("args", []):
        found |= ops_used(a)
    return found


def eval_core(expr, env: dict):
    """Evaluate a rebuild using only the official rules of the core pieces."""
    if isinstance(expr, str):
        return env[expr]
    op = expr["op"]
    if op == "not":
        return OFFICIAL_CONNECTIVES["Negation"]([eval_core(expr["arg"], env)])
    if op == "and":
        return OFFICIAL_CONNECTIVES["Conjunction"]([eval_core(a, env) for a in expr["args"]])
    if op == "and_each":
        return OFFICIAL_CONNECTIVES["Conjunction"]([eval_core(expr["each"], {**env, "$c": c}) for c in env["components"]])
    if op == "forall":
        things, holds = env["things"], env["holds"]
        # The body is evaluated once per thing the bound name could stand for.
        return OFFICIAL_QUANTIFIERS["UniversalQuantification"](
            things, {x for x in things if eval_core(expr["body"], {**env, "body": x in holds})})
    raise ValueError(f"not a core operation: {op}")


def render(expr) -> str:
    if isinstance(expr, str):
        return {"$c": "Ci", "body": "body"}.get(expr, expr)
    op = expr["op"]
    if op == "not":
        inner = render(expr["arg"])
        return f"not {inner}" if isinstance(expr["arg"], str) else f"not ({inner})"
    if op == "and":
        return " and ".join(render(a) if isinstance(a, str) or a["op"] == "not" and isinstance(a["arg"], str) else f"({render(a)})" for a in expr["args"])
    if op == "and_each":
        one = render(expr["each"])
        return f"{one.replace('Ci', 'C1')} and … and {one.replace('Ci', 'Cn')}"
    if op == "forall":
        return f"for every x, {render(expr['body'])}"
    raise ValueError(op)


def tv(b: bool) -> str:
    return "true" if b else "false"


def check(spec: dict) -> dict:
    results = {}
    for name, rec in spec["classes"].items():
        out = {"role": rec["role"], "row": rec["row"]}
        if name in OFFICIAL_CONNECTIVES:
            rule = OFFICIAL_CONNECTIVES[name]
            n_show = 2 if 2 in rec["arity"] else rec["arity"][0]
            out["table"] = {"columns": [f"C{i + 1}" for i in range(n_show)] + [name],
                            "rows": [[tv(c) for c in cs] + [tv(rule(list(cs)))]
                                     for cs in itertools.product([True, False], repeat=n_show)]}
            if rec["role"] == "rebuilt":
                cases, bad = 0, []
                for n in rec["arity"]:
                    for cs in itertools.product([True, False], repeat=n):
                        env = {"components": list(cs), **{f"C{i + 1}": c for i, c in enumerate(cs)}}
                        cases += 1
                        if eval_core(rec["rebuilt_as"], env) != rule(list(cs)):
                            bad.append([tv(c) for c in cs])
                out.update(cases=cases, scope=f"every true/false combination for {', '.join(map(str, rec['arity']))} component(s)")
                out["counterexamples"] = bad
        elif name in OFFICIAL_QUANTIFIERS:
            rule = OFFICIAL_QUANTIFIERS[name]
            things = ["a", "b", "c"]
            out["table"] = {"columns": ["the body is true of", name],
                            "rows": [[f"{k} of 3 things", tv(rule(things, set(things[:k])))] for k in range(4)]}
            if rec["role"] == "rebuilt":
                cases, bad = 0, []
                for size in WORLD_SIZES:
                    world = things[:size]
                    for k in range(size + 1):
                        for holds in itertools.combinations(world, k):
                            cases += 1
                            env = {"things": world, "holds": set(holds)}
                            if eval_core(rec["rebuilt_as"], env) != rule(world, set(holds)):
                                bad.append({"things": world, "body_true_of": list(holds)})
                out.update(cases=cases, scope="every world of 1 to 3 things and every choice of which things the body is true of; a check on small worlds, not a proof")
                out["counterexamples"] = bad
        if rec["role"] == "rebuilt":
            extra = ops_used(rec["rebuilt_as"]) - CORE_OPS
            if extra:
                raise ValueError(f"{name}: rebuild uses non-core operations {sorted(extra)}")
            out["rebuilt_as"] = render(rec["rebuilt_as"])
            out["agrees"] = not out["counterexamples"]
        results[name] = out
    return {"format": "cl-meaning-checks/v1", "generated_by": "scripts/cl_meaning.py",
            "source": spec["source"], "core": spec["core"], "classes": results}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = ap.parse_args()
    result = check(json.loads(args.spec.read_text()))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    failed = 0
    for name, r in result["classes"].items():
        if r["role"] == "rebuilt":
            failed += not r["agrees"]
            print(f"{'AGREES' if r['agrees'] else 'DISAGREES'} {name} = {r['rebuilt_as']}: {r['cases']} cases"
                  + (f", counterexamples {r['counterexamples']}" if r["counterexamples"] else ""))
        else:
            print(f"{r['role'].upper():9s} {name} ({r['row']})")
    print(f"RESULT rebuilds_checked={sum(r['role'] == 'rebuilt' for r in result['classes'].values())} disagreements={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
