# gen_slides v4 — modular pipeline
# PPTX → Structured JSON → HTML
from .src.extractor import extract, extract_pptx, classify_slide, is_placeholder
from .src.renderer_v4 import render, render_html, build_tokens
from .src.upgrader import upgrade, inject_headings, inject_stats, semantic_upgrade
from .src.themes import THEMES, get_theme, list_themes