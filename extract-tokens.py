#!/usr/bin/env python3
"""
extract-tokens.py — Design Token 自動提取與比對工具

掃描 showcase/ 下三套 HTML，提取 CSS custom properties，
輸出 diff 報告。exit code 非零 = token 缺漏（可做 CI gate）。
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

SHOWCASE = Path(__file__).parent / "showcase"
FILES = [
    "aps-ai-agent.html",
    "cris-impacts-carbon.html",
    "runs-impacts-aps-partner.html",
]

# 語意化分類規則
CATEGORY_RULES = [
    (r"^--(c|ink)-\d+$",                    "Color Palette", "🎨"),
    (r"^--(c|ink)-(t[1-4]|[a-z]+(-[a-z]+)*)$", "Semantic Colors", "🎨"),
    (r"^--s\d+$",                           "Spacing (8px grid)", "📏"),
    (r"^--blur(-\d+|-[a-z]+)*$",            "Blur", "🔮"),
    (r"^--t-(fast|mid|slow)$",              "Timing", "⏱️"),
    (r"^--r-(sm|md|lg|xl)$",                "Border Radius", "🔲"),
    (r"^--(border|border-md|border-a)$",    "Border", "🔲"),
    (r"^--ease",                            "Easing", "⏱️"),
    (r"^--(accent|accent-2|accent-mid|accent-(amber|blue|em|rose))$", "Accent", "🎨"),
    (r"^--(text-display|display)-\d+$",     "Display Scale", "🔤"),
    (r"^--(heading|heading-\d+)$",          "Heading Scale", "🔤"),
    (r"^--(body|body-\d+)$",                "Body Scale", "🔤"),
    (r"^--shadow$",                         "Shadow", "🖤"),
    (r"^--(surface|surface-h)$",            "Surface", "🖤"),
    (r"^--(c-glass|c-surface|c-surface2|c-border)$", "Material", "🖤"),
    (r"^--c-(bg|bg2|bg3)$",                "Background", "🖤"),
    # Project-specific: color names and layout
    (r"^--(blue|violet|dark|deep|em|muted|card|mesh|section)$", "Project Theme", "🎭"),
    (r"^--d-.*$",                           "Data Attributes", "⚙️"),
    (r"^--display$",                        "Display Scale", "🔤"),
]

LABELS = {
    "aps-ai-agent.html":                  "APS",
    "cris-impacts-carbon.html":           "CRIS",
    "runs-impacts-aps-partner.html":      "潤思",
}


# ── APS-only allowlist ────────────────────────────────────────────────
# Tokens that are intentionally single-product (APS extensions, spacing variants).
# These are NOT cross-product gaps — filtering them prevents false-positive CI failures.
def load_aps_allowlist() -> set:
    try:
        tokens_path = SHOWCASE / "tokens.json"
        with open(tokens_path) as f:
            data = json.load(f)
        aps_only = set()
        aps_map = data.get("mapping_table", {}).get("aps_to_canonical", {})
        for cat in data.get("categories", {}).values():
            for name, info in cat.get("tokens", {}).items():
                # APS flag set, but no canonical mapping = APS-only extension
                if info.get("aps") and name not in aps_map:
                    aps_only.add(name)
        return aps_only
    except Exception:
        return set()

APS_ONLY_ALLOWLIST = load_aps_allowlist()


# ── Token extraction ──────────────────────────────────────────────────
def extract_tokens(html_path):
    text = html_path.read_text(encoding="utf-8")
    tokens = set()
    for m in re.finditer(r'--([a-zA-Z][a-zA-Z0-9-]*)', text):
        tokens.add(f"--{m.group(1)}")
    return tokens


def categorize(token):
    for pattern, label, emoji in CATEGORY_RULES:
        if re.match(pattern, token):
            return label, emoji
    return "Other", "📦"


# ── Report: diff with allowlist ───────────────────────────────────────
def diff_report(file_tokens):
    all_tokens = set()
    for tokens in file_tokens.values():
        all_tokens |= tokens

    categorized = defaultdict(lambda: {"tokens": set(), "files": defaultdict(bool)})
    for token in sorted(all_tokens):
        cat, emoji = categorize(token)
        categorized[(emoji, cat)]["tokens"].add(token)
        for fname, tokens in file_tokens.items():
            categorized[(emoji, cat)]["files"][fname] = categorized[(emoji, cat)]["files"].get(fname, defaultdict(bool))
            categorized[(emoji, cat)]["files"][fname][token] = token in tokens

    issues = 0
    lines = ["=" * 72, "  Design Token Diff Report", "=" * 72, ""]

    for (emoji, cat), data in sorted(categorized.items()):
        lines.append(f"  {emoji} {cat}")
        lines.append(f"  {'─' * 40}")
        for token in sorted(data["tokens"]):
            aps_ok = "✅" if token in file_tokens["aps-ai-agent.html"] else "❌"
            cris_ok = "✅" if token in file_tokens["cris-impacts-carbon.html"] else "❌"
            runs_ok = "✅" if token in file_tokens["runs-impacts-aps-partner.html"] else "❌"
            # Allowlist: APS-only tokens intentionally absent from other products
            if APS_ONLY_ALLOWLIST and token in APS_ONLY_ALLOWLIST:
                _aps = 0 if aps_ok == "✅" else 1  # APS missing = real gap
                _cris = 0  # APS-only, not a cross-product gap
                _runs = 0  # APS-only, not a cross-product gap
            else:
                _aps = 0 if aps_ok == "✅" else 1
                _cris = 0 if cris_ok == "✅" else 1
                _runs = 0 if runs_ok == "✅" else 1
            m = _aps + _cris + _runs
            if m > 0:
                issues += m
            lines.append(f"  {token:<28} {aps_ok:<6} {cris_ok:<6} {runs_ok:<6}")
        lines.append("")

    aps_t = len(file_tokens["aps-ai-agent.html"])
    cris_t = len(file_tokens["cris-impacts-carbon.html"])
    runs_t = len(file_tokens["runs-impacts-aps-partner.html"])
    common = len(file_tokens["aps-ai-agent.html"] & file_tokens["cris-impacts-carbon.html"] & file_tokens["runs-impacts-aps-partner.html"])
    union = len(all_tokens)

    lines += ["=" * 72, "  Summary", "=" * 72, ""]
    lines.append(f"  APS  tokens: {aps_t}")
    lines.append(f"  CRIS tokens: {cris_t}")
    lines.append(f"  潤思 tokens: {runs_t}")
    lines.append(f"  Common (all 3): {common}")
    lines.append(f"  Union:          {union}")
    lines.append(f"  Missing slots:  {issues}")
    if APS_ONLY_ALLOWLIST:
        lines.append(f"  (filtered {len(APS_ONLY_ALLOWLIST)} APS-only tokens)")
    lines.append("")

    lines.append("  Unique tokens per file:")
    for fname in FILES:
        label = LABELS[fname]
        others = set()
        for of in FILES:
            if of != fname:
                others |= file_tokens[of]
        unique = file_tokens[fname] - others
        if unique:
            lines.append(f"  {label}: {', '.join(sorted(unique))}")

    lines.append("")
    lines.append(f"  ❌ {issues} missing token slots detected." if issues > 0 else "  ✅ All tokens consistent across 3 files.")
    return "\n".join(lines), issues


# ── Report: JSON (CI-friendly) ────────────────────────────────────────
def json_report(file_tokens):
    all_tokens = set()
    for tokens in file_tokens.values():
        all_tokens |= tokens

    token_matrix = {}
    for token in sorted(all_tokens):
        cat_label, _ = categorize(token)
        token_matrix[token] = {
            "category": cat_label,
            "APS": token in file_tokens["aps-ai-agent.html"],
            "CRIS": token in file_tokens["cris-impacts-carbon.html"],
            "潤思": token in file_tokens["runs-impacts-aps-partner.html"],
        }

    aps_set = file_tokens["aps-ai-agent.html"]
    cris_set = file_tokens["cris-impacts-carbon.html"]
    runs_set = file_tokens["runs-impacts-aps-partner.html"]
    common = aps_set & cris_set & runs_set

    missing = sum(
        (0 if token_matrix[t]["APS"] else 1) +
        (0 if (APS_ONLY_ALLOWLIST and t in APS_ONLY_ALLOWLIST) else (0 if token_matrix[t]["CRIS"] else 1)) +
        (0 if (APS_ONLY_ALLOWLIST and t in APS_ONLY_ALLOWLIST) else (0 if token_matrix[t]["潤思"] else 1))
        for t in token_matrix
    )

    output = {
        "summary": {
            "APS_tokens": len(aps_set),
            "CRIS_tokens": len(cris_set),
            "潤思_tokens": len(runs_set),
            "common": len(common),
            "union": len(all_tokens),
            "missing_slots": missing,
            "aps_only_filtered": len(APS_ONLY_ALLOWLIST) if APS_ONLY_ALLOWLIST else 0,
        },
        "unique_per_file": {
            "APS": sorted(aps_set - cris_set - runs_set),
            "CRIS": sorted(cris_set - aps_set - runs_set),
            "潤思": sorted(runs_set - aps_set - cris_set),
        },
        "common": sorted(common),
        "tokens": token_matrix,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return missing


# ── Check mode (CI gate) ──────────────────────────────────────────────
def check_mode(file_tokens):
    """Check-only mode: exit code = missing slot count.
    APS-only allowlist auto-applied if loaded."""
    all_tokens = set()
    for tokens in file_tokens.values():
        all_tokens |= tokens

    missing = 0
    dbg = 0
    for token in sorted(all_tokens):
        aps = token in file_tokens["aps-ai-agent.html"]
        cris = token in file_tokens["cris-impacts-carbon.html"]
        runs = token in file_tokens["runs-impacts-aps-partner.html"]
        if APS_ONLY_ALLOWLIST and token in APS_ONLY_ALLOWLIST:
            _aps = 0 if aps else 1
            _cris = 0
            _runs = 0
        else:
            _aps = 0 if aps else 1
            _cris = 0 if cris else 1
            _runs = 0 if runs else 1
        slot = _aps + _cris + _runs
        if dbg < 5 and slot > 0:
            import sys as _s
            print(f"  [CM] {token}: aps={aps} cris={cris} runs={runs} -> {slot}", file=_s.stderr)
            dbg += 1
        missing += slot

    if missing > 0:
        print(f"❌ {missing} missing token slots")
    else:
        print("✅ All tokens consistent across 3 files")
    return missing


# ── Main ──────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Design Token 自動提取與比對工具")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    parser.add_argument("--check", action="store_true", help="Check-only mode（無輸出細節，僅 exit code）")
    parser.add_argument("--files", nargs="*", help="指定檔案，預設掃描 showcase/*.html")
    args = parser.parse_args()

    target_files = args.files if args.files else FILES

    file_tokens = {}
    missing_files = []

    for fname in target_files:
        path = SHOWCASE / fname
        if not path.exists():
            missing_files.append(fname)
            file_tokens[fname] = set()
        else:
            file_tokens[fname] = extract_tokens(path)

    if missing_files:
        print(f"⚠️  Missing files: {missing_files}")
        sys.exit(2)

    if args.check:
        issues = check_mode(file_tokens)
    elif args.json:
        issues = json_report(file_tokens)
    else:
        report, issues = diff_report(file_tokens)
        print(report)

    sys.exit(min(issues, 255))


if __name__ == "__main__":
    main()
