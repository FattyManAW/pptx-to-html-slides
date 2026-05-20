#!/usr/bin/env python3
"""
extract-tokens.py — Design Token 自動提取與比對工具

掃描 showcase/ 下三套 HTML，提取 CSS custom properties，
輸出 diff 報告。exit code 非零 = token 缺漏（可做 CI gate）。
"""

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
    # (regex pattern, label, category)
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

def extract_tokens(html_path):
    """提取 HTML 中所有 CSS custom properties"""
    text = html_path.read_text(encoding="utf-8")
    tokens = set()
    for m in re.finditer(r'--([a-zA-Z][a-zA-Z0-9-]*)', text):
        tokens.add(f"--{m.group(1)}")
    return tokens

def categorize(token):
    """將 token 歸入語意分類"""
    for pattern, label, emoji in CATEGORY_RULES:
        if re.match(pattern, token):
            return label, emoji
    return "Other", "📦"

def diff_report(file_tokens):
    """產出 diff 報告"""
    all_tokens = set()
    for tokens in file_tokens.values():
        all_tokens |= tokens

    # Group by category
    categorized = defaultdict(lambda: {"tokens": set(), "files": defaultdict(bool)})
    for token in sorted(all_tokens):
        cat, emoji = categorize(token)
        categorized[(emoji, cat)]["tokens"].add(token)
        for fname, tokens in file_tokens.items():
            categorized[(emoji, cat)]["files"][fname] = categorized[(emoji, cat)]["files"].get(fname, defaultdict(bool))
            categorized[(emoji, cat)]["files"][fname][token] = token in tokens

    issues = 0
    lines = []
    lines.append("=" * 72)
    lines.append("  Design Token Diff Report")
    lines.append("=" * 72)
    lines.append("")

    for (emoji, cat), data in sorted(categorized.items()):
        lines.append(f"  {emoji} {cat}")
        lines.append(f"  {'─' * 40}")
        tokens_sorted = sorted(data["tokens"])

        # Table header
        header = f"  {'Token':<28} {'APS':<6} {'CRIS':<6} {'潤思':<6}"
        lines.append(header)
        lines.append(f"  {'─' * 46}")

        cat_issues = 0
        for token in tokens_sorted:
            aps_ok = "✅" if token in file_tokens["aps-ai-agent.html"] else "❌"
            cris_ok = "✅" if token in file_tokens["cris-impacts-carbon.html"] else "❌"
            runs_ok = "✅" if token in file_tokens["runs-impacts-aps-partner.html"] else "❌"
            missing = sum(1 for x in [aps_ok, cris_ok, runs_ok] if x == "❌")
            if missing > 0:
                cat_issues += missing
                issues += missing

            lines.append(f"  {token:<28} {aps_ok:<6} {cris_ok:<6} {runs_ok:<6}")

        lines.append("")

    # Summary
    lines.append("=" * 72)
    lines.append("  Summary")
    lines.append("=" * 72)
    aps_tokens = len(file_tokens["aps-ai-agent.html"])
    cris_tokens = len(file_tokens["cris-impacts-carbon.html"])
    runs_tokens = len(file_tokens["runs-impacts-aps-partner.html"])
    common = len(file_tokens["aps-ai-agent.html"] & file_tokens["cris-impacts-carbon.html"] & file_tokens["runs-impacts-aps-partner.html"])
    union = len(all_tokens)

    lines.append(f"  APS  tokens: {aps_tokens}")
    lines.append(f"  CRIS tokens: {cris_tokens}")
    lines.append(f"  潤思 tokens: {runs_tokens}")
    lines.append(f"  Common (all 3): {common}")
    lines.append(f"  Union:          {union}")
    lines.append(f"  Missing slots:  {issues}")
    lines.append("")

    # Per-file unique tokens
    lines.append("  Unique tokens per file:")
    for fname in FILES:
        label = LABELS[fname]
        other_files = [FILES[i] for i in range(len(FILES)) if FILES[i] != fname]
        others_union = set()
        for of in other_files:
            others_union |= file_tokens[of]
        unique = file_tokens[fname] - others_union
        if unique:
            lines.append(f"  {label}: {', '.join(sorted(unique))}")

    lines.append("")
    if issues > 0:
        lines.append(f"  ❌ {issues} missing token slots detected.")
    else:
        lines.append(f"  ✅ All tokens consistent across 3 files.")

    return "\n".join(lines), issues


def json_report(file_tokens):
    """JSON 格式輸出，適合 CI 解析"""
    import json
    all_tokens = set()
    for tokens in file_tokens.values():
        all_tokens |= tokens

    token_matrix = {}
    for token in sorted(all_tokens):
        cat_label, cat_emoji = categorize(token)
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
        3 - token_matrix[t]["APS"] - token_matrix[t]["CRIS"] - token_matrix[t]["潤思"]
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


def check_mode(file_tokens):
    """Check-only mode: 有缺漏時 exit code = 缺漏數"""
    all_tokens = set()
    for tokens in file_tokens.values():
        all_tokens |= tokens

    missing = 0
    for token in sorted(all_tokens):
        aps = token in file_tokens["aps-ai-agent.html"]
        cris = token in file_tokens["cris-impacts-carbon.html"]
        runs = token in file_tokens["runs-impacts-aps-partner.html"]
        count = aps + cris + runs
        if count < 3:
            missing += 3 - count

    if missing > 0:
        print(f"❌ {missing} missing token slots")
    else:
        print("✅ All tokens consistent across 3 files")
    return missing


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