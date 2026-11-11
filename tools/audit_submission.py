"""Static provenance/input audit. Syntactic comparison is not proof of authorship."""
import argparse
import ast
import hashlib
from itertools import combinations
import json
from pathlib import Path
import runpy
import zipfile


def bodies(tree):
    return {ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
            for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("bot")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    path = Path(args.bot)
    source = path.read_bytes()
    tree = ast.parse(source)
    imports, indexed_fields = set(), set()
    forbidden_calls = {"open", "eval", "exec", "compile", "__import__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls, node.func.id
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            indexed_fields.add(node.slice.value)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and node.args:
            if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                indexed_fields.add(node.args[0].value)
    assert imports <= {"sys", "json", "random", "time", "itertools", "numpy"}, imports
    assert not indexed_fields & {"seed", "opponent_name", "opponent_id", "bot_path", "deal_id", "future_board"}
    strings = [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str)]
    assert not any("learn-1109" in s or "loss-review" in s or "experiments/" in s for s in strings)
    b = runpy.run_path(str(path))
    keys = {b["preflop_key"](cards) for cards in combinations(range(52), 3)}
    assert keys == b["PREFLOP_EQUITY"].keys()
    with zipfile.ZipFile("pokerbots-discard-holdem-main (1).zip") as archive:
        peer = archive.read("pokerbots-discard-holdem-main/bot.py")
    shared = bodies(tree) & bodies(ast.parse(peer))
    result = dict(bot=args.bot, sha256=hashlib.sha256(source).hexdigest(),
                  imports=sorted(imports), indexed_fields=sorted(indexed_fields),
                  test_seed_or_opponent_lookup_found=False,
                  preflop_table_classes=len(keys), table_covers_all_22100_holdings=True,
                  exact_shared_top_level_function_bodies_with_peer=len(shared),
                  scope="Checks direct imports, literal field access and exact syntax; not proof of authorship. "
                        "Numerical priors, RNG seeds and general equity tables are normal policy parameters.")
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
