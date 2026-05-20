"""
upgrader.py — Semantic Injection (gen_slides v4 module)

提供：
- upgrade(spec) → enriched spec（semantic hierarchy + token injection）
- inject_semantic(spec) → add headings, feature grids, stat nums
"""


def upgrade(spec):
    """
    對 v4 spec 執行語義注入。
    回傳增強後的 spec（不改變原始結構）。
    """
    slides = spec.get("slides", [])
    enriched = []

    for s in slides:
        blocks = s.get("blocks", [])
        etype = s.get("type", "content")

        # Content slides：將第一個 block 提升為 h2（如果還沒有標題層次）
        if etype == "content" and blocks and "t" not in s:
            s["t"] = blocks[0]

        # Items slides：確認 cards 格式
        if etype == "items" and "items" in s:
            for card in s["items"]:
                if "ls" not in card:
                    card["ls"] = []

        enriched.append(s)

    spec["slides"] = enriched
    return spec


def inject_headings(spec):
    """為所有 content slide 注入 h2 heading 標記。"""
    for s in spec.get("slides", []):
        if s.get("type") == "content" and "t" not in s:
            blocks = s.get("blocks", [])
            if blocks:
                s["t"] = blocks[0]
    return spec


def inject_stats(spec):
    """標記統計數字區塊。"""
    import re
    for s in spec.get("slides", []):
        blocks = s.get("blocks", [])
        stats = []
        for block in blocks:
            # 尋找數字 + 單位模式
            m = re.search(r"(\d[\d,.]*)\s*([%％萬万亿kW])", block)
            if m:
                stats.append({"value": m.group(1), "unit": m.group(2), "label": block[:40]})
        if stats:
            s["stats"] = stats
    return spec


# 向後相容別名
semantic_upgrade = upgrade