"""
canonical_map.py — Token Canonicalization (gen_slides v4 module)

提供：load_mappings() + apply_shim()
從 tokens.json 載入 APS→Canonical 映射表，在 CSS 渲染時自動注入。

用法：
  from .canonical_map import load_mappings, apply_shim
  mappings = load_mappings()
  css = apply_shim(css, mappings)
"""

import json
import re
import os
import sys

# 尋找 tokens.json（相對於 showcase/）
def _find_tokens():
    dirs = [
        os.path.join(os.path.dirname(__file__), "..", "..", "showcase", "tokens.json"),
        os.path.join(os.path.dirname(__file__), "..", "showcase", "tokens.json"),
    ]
    for d in dirs:
        path = os.path.normpath(d)
        if os.path.isfile(path):
            return path
    return None


def load_mappings():
    """
    從 tokens.json 載入映射表。
    回傳: { "aps_to_canonical": dict, "ds_tokens": dict }
    """
    path = _find_tokens()
    if not path:
        return {"aps_to_canonical": {}, "ds_tokens": {}}

    with open(path) as f:
        data = json.load(f)

    mt = data.get("mapping_table", {})
    aps_to_canonical = mt.get("aps_to_canonical", {})

    # 提取 --ds-* tokens
    ds_tokens = {}
    cats = data.get("categories", {})
    if isinstance(cats, dict):
        for cat_data in cats.values():
            if isinstance(cat_data, dict):
                tokens = cat_data.get("tokens", {})
                # tokens can be dict of {name: {value, aps, cris, runs}} or list
                if isinstance(tokens, dict):
                    for name, tinfo in tokens.items():
                        if isinstance(tinfo, dict) and name.startswith("--ds-"):
                            ds_tokens[name] = tinfo.get("value", "")
    elif isinstance(cats, list):
        for cat_data in cats:
            if isinstance(cat_data, dict):
                tokens = cat_data.get("tokens", [])
                if isinstance(tokens, list):
                    for t in tokens:
                        name = t.get("name", "")
                        if name.startswith("--ds-"):
                            ds_tokens[name] = t.get("value", "")

    return {
        "aps_to_canonical": aps_to_canonical,
        "ds_tokens": ds_tokens,
    }


def apply_shim(html: str, mappings: dict) -> str:
    """
    對 HTML 內容執行 canonical shim 注入：
    1. 在 :root {} 注入 --ds-* tokens
    2. CSS definition: --c-950 → --ink-950
    3. var() reference: var(--c-950) → var(--ink-950)

    回傳: 改造後的 HTML
    """
    if not mappings:
        return html

    aps_to_canonical = mappings.get("aps_to_canonical", {})
    ds_tokens = mappings.get("ds_tokens", {})

    # Step 1: 注入 --ds-* tokens 到第一組 :root {} block
    if ds_tokens:
        ds_lines = ["  /* --ds-* Canonical Design Intent */"]
        for name, value in sorted(ds_tokens.items()):
            ds_lines.append(f"  {name}: {value};")
        ds_block = "\n".join(ds_lines)
        html = html.replace(
            ":root {",
            f":root {{\n{ds_block}",
            1
        )

    # Step 2: 映射 CSS token 定義名稱
    for old_name, new_name in aps_to_canonical.items():
        # 只替換定義（:root block 內的），不是 var() usage
        # pattern:  --c-950: 或  --c-950: （行首或空格開頭）
        html = re.sub(
            r'(^|\s+|\n\s*)' + re.escape(old_name) + r'(\s*:)',
            r'\1' + new_name + r'\2',
            html
        )

    # Step 3: 映射 var() 參照
    for old_name, new_name in aps_to_canonical.items():
        html = html.replace(f"var({old_name})", f"var({new_name})")
        html = html.replace(f"var({old_name},", f"var({new_name},")

    return html


def remap_html_file(input_path: str, output_path: str = None):
    """
    對已存在的 HTML 檔案執行 canonical shim。
    適用於 --canonical flag：增量升級現有 HTML。
    """
    with open(input_path) as f:
        html = f.read()

    mappings = load_mappings()
    html = apply_shim(html, mappings)

    out = output_path or input_path
    with open(out, "w") as f:
        f.write(html)

    return len(mappings.get("aps_to_canonical", {})), len(mappings.get("ds_tokens", {}))