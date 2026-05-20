"""
themes.py — Design System Themes (extracted from gen_slides_v4.py)

提供：THEMES dict（cris / aps / runs）+ 輔助函式
"""

THEMES = {
    "cris": {
        "name": "CRIS IMPACTs — Teal Carbon",
        "colors": {
            "ink50": "#f8fafc", "ink100": "#f1f5f9", "ink200": "#e2e8f0",
            "ink300": "#cbd5e1", "ink400": "#94a3b8", "ink500": "#64748b",
            "ink600": "#475569", "ink700": "#334155", "ink800": "#1e293b",
            "ink900": "#0f172a", "ink950": "#06080d",
            "accent": "#14b8a6", "accentMid": "#2dd4bf",
            "surface": "rgba(255,255,255,.04)", "surfaceH": "rgba(255,255,255,.07)",
            "border": "rgba(255,255,255,.08)", "borderA": "rgba(20,184,166,.12)",
            "c-bg": "#050810", "c-bg2": "#0a1018", "c-bg3": "#0f1620",
            "c-surface": "rgba(255,255,255,.04)", "c-surface2": "rgba(255,255,255,.07)",
            "c-teal": "#14b8a6", "c-teal-dim": "rgba(20,184,166,.12)",
            "c-teal-glow": "rgba(20,184,166,.25)", "c-teal-hot": "#2dd4bf",
            "c-t1": "#f0f4f8", "c-t2": "#94a3b8", "c-t3": "#64748b", "c-t4": "#3b5068",
            "c-error": "#ef4444", "c-success": "#22c55e", "c-warning": "#f59e0b", "c-info": "#3b82f6",
        },
    },
    "aps": {
        "name": "APS AI Agent — Multi-Accent",
        "colors": {
            "accent": "#635bff", "accent-2": "#a78bfa",
            "accent-amber": "#f59e0b", "accent-blue": "#3b82f6",
            "accent-em": "#ec4899", "accent-rose": "#f43f5e",
            "c-600": "#475569", "c-700": "#334155", "c-800": "#1e293b",
            "c-900": "#0f172a", "c-950": "#020617",
            "c-t1": "rgba(255,255,255,.95)", "c-t2": "rgba(255,255,255,.72)",
            "c-t3": "rgba(255,255,255,.46)", "c-t4": "rgba(255,255,255,.28)",
            "c-error": "#ef4444", "c-error-dim": "rgba(239,68,68,.12)",
            "c-success": "#22c55e", "c-success-dim": "rgba(34,197,94,.12)",
            "c-warning": "#f59e0b", "c-warning-dim": "rgba(245,158,11,.12)",
            "c-info": "#3b82f6", "c-info-dim": "rgba(59,130,246,.12)",
        },
    },
    "runs": {
        "name": "潤思 IMPACTs — Teal Carbon",
        "colors": {
            "ink50": "#f8fafc", "ink100": "#f1f5f9", "ink200": "#e2e8f0",
            "ink300": "#cbd5e1", "ink400": "#94a3b8", "ink500": "#64748b",
            "ink600": "#475569", "ink700": "#334155", "ink800": "#1e293b",
            "ink900": "#0f172a", "ink950": "#06080d",
            "accent": "#14b8a6", "accentMid": "#2dd4bf",
            "surface": "rgba(255,255,255,.04)", "surfaceH": "rgba(255,255,255,.07)",
            "border": "rgba(255,255,255,.08)", "borderA": "rgba(20,184,166,.12)",
            "c-bg": "#050810", "c-t1": "#f0f4f8", "c-t2": "#94a3b8",
            "c-t3": "#64748b", "c-t4": "#3b5068",
            "c-teal": "#14b8a6", "c-teal-hot": "#2dd4bf",
        },
    },
}


def list_themes():
    """列出所有可用主題。"""
    return [(k, t["name"]) for k, t in THEMES.items()]


def get_theme(name="cris"):
    """獲取指定主題，fallback 到 cris。"""
    return THEMES.get(name, THEMES["cris"])


# 從 v4 提取的常數 — 保留向後相容 import *
PLACEHOLDER_PATTERNS = [
    r"添加文本", r"单击此处添加标题", r"单击此处添加副标题",
    r"单击此处添加文本", r"點擊此處", r"Click to add",
]

SECTION_KEYWORDS = [
    "目標客戶", "核心功能", "技術架構", "解決方案", "實施案例",
    "競爭優勢", "市場分析", "產品介紹", "團隊介紹", "發展規劃",
    "政策", "趨勢", "挑戰", "現狀", "痛點",
    "為什麼", "如何實現", "平台架構", "應用場景",
    "合作夥伴", "關於我們", "未來展望", "行業應用",
    "產品", "服務", "功能", "優勢", "案例",
]

COMPARISON_KEYWORDS = [
    ("挑戰", "方案"), ("痛點", "解決"), ("問題", "對策"),
    ("傳統", "數位"), ("現狀", "目標"), ("Before", "After"),
]