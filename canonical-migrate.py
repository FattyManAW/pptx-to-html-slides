#!/usr/bin/env python3
"""
canonical-migrate.py — Compat Shim → Full Canonical Migration

Maps:  --ds-X: var(--Y)  (shim definition)
To:    var(--Y)  →  var(--ds-X)  (in rules)

Strategy:
  1. Parse the shim block to build --ds-X → --Y mapping table
  2. Scan the entire CSS for var(--Y) uses outside the shim
  3. Replace with var(--ds-X)
  4. Keep the shim block intact for external compat
  5. Report migration stats

Usage:
  python3 canonical-migrate.py <input.html> [--output <output.html>] [--dry-run]
"""

import re
import sys
import os
from collections import OrderedDict

SHIM_START = re.compile(r'/\*.*?--ds-\*.*?Compat\s+Shim', re.IGNORECASE)
SHIM_END = re.compile(r'/\*.*?End\s+--ds-\*', re.IGNORECASE)
SHIM_VAR = re.compile(r'(--ds-[\w-]+)\s*:\s*var\((--[\w-]+)\)')

def parse_shim(css: str) -> 'OrderedDict[str, str]':
    """Parse --ds-X: var(--Y) mappings from the compat shim block."""
    mapping = OrderedDict()
    
    # Find shim block boundaries
    start = SHIM_START.search(css)
    end = SHIM_END.search(css)
    if not start or not end:
        print("⚠️  No compat shim block found")
        return mapping
    
    shim_block = css[start.start():end.end()]
    for m in SHIM_VAR.finditer(shim_block):
        canonical = m.group(1)   # --ds-c-bg
        legacy = m.group(2)       # --c-bg
        if legacy not in mapping.values():
            mapping[canonical] = legacy
    
    return mapping


def build_replacement_map(mapping: 'OrderedDict[str, str]') -> dict:
    """Build legacy→canonical replacement map. Handle partial overlaps carefully."""
    repl = {}
    # Sort by legacy name length descending so longer names match first
    sorted_entries = sorted(mapping.items(), key=lambda x: len(x[1]), reverse=True)
    
    for canonical, legacy in sorted_entries:
        # For CSS var() references: var(--legacy) → var(--canonical)
        if legacy not in repl:
            repl[legacy] = canonical
    
    return repl


def migrate_css(css: str, dry_run: bool = False) -> 'tuple[str, int]':
    """Replace var(--legacy) with var(--ds-canonical) outside the shim block."""
    mapping = parse_shim(css)
    if not mapping:
        return css, 0
    
    repl_map = build_replacement_map(mapping)
    
    # Find shim boundaries to protect
    start = SHIM_START.search(css)
    end = SHIM_END.search(css)
    
    if start and end:
        before = css[:start.start()]
        shim_body = css[start.start():end.end()]
        after = css[end.end():]
    else:
        before = css
        shim_body = ''
        after = ''
    
    # Build replacement regex: match var(--legacy-name)
    # Sort by length descending for greedy replacement
    legacies = sorted(repl_map.keys(), key=len, reverse=True)
    var_pattern = re.compile(
        r'var\((' + '|'.join(re.escape(l) for l in legacies) + r')\b'
    )
    
    def _replace(m):
        legacy = m.group(1)
        canonical = repl_map[legacy]
        return f'var({canonical}'
    
    count = 0
    
    def _migrate_section(text: str) -> str:
        nonlocal count
        result = var_pattern.sub(lambda m: (_replace(m), inc())[0], text)
        
        def inc():
            nonlocal count
            count += 1
            return None
        # Redo: need a proper counter
        return text  # placeholder
    
    # Actually do the replacement properly
    before_replaced, n1 = var_pattern.subn(_replace, before)
    after_replaced, n2 = var_pattern.subn(_replace, after)
    
    total = n1 + n2
    
    if dry_run:
        print(f"  → Would replace {total} var() references across {len(mapping)} tokens")
        for canonical, legacy in list(mapping.items())[:10]:
            print(f"    var({legacy}) → var({canonical})")
        if len(mapping) > 10:
            print(f"    ... and {len(mapping)-10} more")
        return css, total
    
    result = before_replaced + shim_body + after_replaced
    return result, total


def migrate_file(input_path: str, output_path: str = None, dry_run: bool = False):
    """Migrate a single HTML file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    migrated, count = migrate_css(content, dry_run=dry_run)
    
    if dry_run:
        return count
    
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}-canonical{ext}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(migrated)
    
    return count


def verify(filepath: str) -> dict:
    """Verify migration: count legacy/--ds-* var() refs."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Exclude shim block
    start = SHIM_START.search(content)
    end = SHIM_END.search(content)
    if start and end:
        check = content[:start.start()] + content[end.end():]
    else:
        check = content
    
    # Count --ds-* references (post-migration)
    ds_refs = len(re.findall(r'var\(--ds-', check))
    
    # Count legacy references that still exist (outside shim)
    legacy_pattern = re.compile(r'var\(--(?!ds-)([a-z][\w-]+)')
    leftover = legacy_pattern.findall(check)
    
    return {
        'ds_refs': ds_refs,
        'legacy_left': len(leftover),
        'legacy_names': sorted(set(leftover)),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = None
    dry_run = '--dry-run' in sys.argv
    
    for i, arg in enumerate(sys.argv):
        if arg == '--output' and i + 1 < len(sys.argv):
            output_path = sys.argv[i + 1]
    
    if dry_run:
        print(f"🔍 DRY RUN: {os.path.basename(input_path)}")
        count = migrate_file(input_path, dry_run=True)
        print(f"  ✅ {count} replacements would be made")
        return
    
    print(f"🔄 Migrating: {os.path.basename(input_path)}")
    count = migrate_file(input_path, output_path)
    
    target = output_path or f"{os.path.splitext(input_path)[0]}-canonical{os.path.splitext(input_path)[1]}"
    stats = verify(target)
    
    print(f"  ✅ {count} var() references migrated")
    print(f"  📊 --ds-* refs: {stats['ds_refs']} | legacy leftover: {stats['legacy_left']}")
    if stats['legacy_left'] > 0:
        print(f"  ⚠️  Remaining legacy: {', '.join(stats['legacy_names'][:8])}")
        if len(stats['legacy_names']) > 8:
            print(f"     ... and {len(stats['legacy_names'])-8} more")
    print(f"  📁 → {target}")


if __name__ == '__main__':
    main()