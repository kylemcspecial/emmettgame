"""Emulate Python 3.9 f-string restrictions across the codebase:
1. No backslash inside f-string expression braces
2. No nested same-type quotes inside the expression of a double-quoted f-string
"""
import ast
import os
import re

issues = []
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv")]
    for fn in sorted(files):
        if not fn.endswith(".py"):
            continue
        p = os.path.join(root, fn)
        src = open(p, encoding="utf-8").read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.JoinedStr):
                seg = ast.get_source_segment(src, node) or ""
                for v in node.values:
                    if isinstance(v, ast.FormattedValue):
                        s2 = ast.get_source_segment(src, v) or ""
                        if "\\" in s2:
                            issues.append((p, v.lineno, "backslash: " + s2[:60]))
                        if '"' in s2 and seg.startswith('f"'):
                            issues.append((p, v.lineno, "nested-quote: " + s2[:60]))
for i in issues:
    print(i)
print("total:", len(issues))
