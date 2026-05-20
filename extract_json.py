#!/usr/bin/env python3
"""Extract JSON from run_qa.py --ci mixed stdout output.
Usage: python3 run_qa.py --ci 2>&1 | python3 extract_json.py > qa_result.json
"""
import sys, json

lines = sys.stdin.readlines()
# Find the outermost { ... } JSON block
start = None
depth = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if start is None:
        if stripped.startswith('{'):
            start = i
    if start is not None:
        depth += stripped.count('{') - stripped.count('}')
        if depth <= 0:
            json_str = ''.join(lines[start:i+1])
            d = json.loads(json_str)
            print(json.dumps(d))
            break
