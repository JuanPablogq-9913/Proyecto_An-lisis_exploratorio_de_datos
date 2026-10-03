"""Hoja de estilos del tablero (inyectada una sola vez en la página)."""

from __future__ import annotations

from ..config import PALETTE

_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600&display=swap"
)

CSS = f"""
<style>
@import url('{_FONTS}');

html, body, [class*="css"], .stMarkdown, .stText {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
    color: {PALETTE.ink};
}}
.block-container {{ padding-top: 2rem; max-width: 1180px; }}

/* Encabezado */
.hero {{
    background: linear-gradient(135deg, #123A6B 0%, {PALETTE.primary} 100%);
    color: #fff; border-radius: 16px; padding: 2rem 2.2rem; margin-bottom: 1.5rem;
}}
.hero .eyebrow {{ text-transform: uppercase; letter-spacing: .08em; font-size: .75rem; opacity: .85; }}
.hero h1 {{
    font-family: 'Fraunces', Georgia, serif; font-size: 2.3rem; line-height: 1.15;
    margin: .35rem 0 .6rem; color: #fff; padding: 0;
}}
.hero p {{ margin: 0; font-size: 1.02rem; opacity: .95; max-width: 760px; }}
.hero .meta {{ margin-top: 1rem; font-size: .85rem; opacity: .85; }}

/* Tarjetas KPI */
.kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: .9rem; }}
.kpi {{
    background: {PALETTE.surface}; border: 1px solid {PALETTE.grid}; border-radius: 12px;
    padding: 1rem 1.1rem; border-top: 4px solid {PALETTE.primary};
}}
.kpi.alert {{ border-top-color: {PALETTE.accent}; }}
.kpi .label {{ font-size: .8rem; color: {PALETTE.ink_muted}; font-weight: 500; }}
.kpi .value {{ font-size: 1.9rem; font-weight: 700; line-height: 1.2; margin: .2rem 0; }}
.kpi.alert .value {{ color: {PALETTE.accent}; }}
.kpi .hint {{ font-size: .78rem; color: {PALETTE.ink_muted}; }}

/* Encabezados de sección */
.section {{ margin: 2.6rem 0 .6rem; }}
.section .eyebrow {{
    font-size: .75rem; font-weight: 600; letter-spacing: .08em; text-transform: uppercase;
    color: {PALETTE.primary};
}}
.section h2 {{ font-family: 'Fraunces', Georgia, serif; font-size: 1.65rem; margin: .2rem 0; padding: 0; }}
.section .question {{ color: {PALETTE.ink_muted}; font-size: 1rem; margin: 0; }}
.chart-title {{ font-weight: 600; font-size: .95rem; margin: .6rem 0 0; }}

/* Lectura interpretativa */
.insight {{
    background: {PALETTE.primary_soft}; border-left: 4px solid {PALETTE.primary};
    border-radius: 0 10px 10px 0; padding: .85rem 1.1rem; font-size: .95rem; line-height: 1.55;
    margin: .2rem 0 1rem;
}}
.insight.alert {{ background: {PALETTE.accent_soft}; border-left-color: {PALETTE.accent}; }}

/* Hallazgos y decisiones */
.finding {{
    background: {PALETTE.surface}; border: 1px solid {PALETTE.grid}; border-radius: 14px;
    padding: 1.2rem 1.3rem; margin-bottom: 1rem;
}}
.finding .tag {{
    display: inline-block; background: {PALETTE.primary_soft}; color: {PALETTE.primary};
    font-size: .72rem; font-weight: 600; padding: .15rem .55rem; border-radius: 99px;
}}
.finding h3 {{ font-size: 1.15rem; margin: .5rem 0 .4rem; padding: 0; }}
.finding .decision {{ font-size: .98rem; line-height: 1.5; margin-bottom: .7rem; }}
.finding dl {{
    display: grid; grid-template-columns: 150px 1fr; gap: .35rem .9rem; margin: 0; font-size: .88rem;
}}
.finding dt {{ color: {PALETTE.ink_muted}; font-weight: 600; }}
.finding dd {{ margin: 0; }}
@media (max-width: 640px) {{ .finding dl {{ grid-template-columns: 1fr; }} }}

/* Pie */
.footer {{
    margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid {PALETTE.grid};
    color: {PALETTE.ink_muted}; font-size: .85rem; line-height: 1.6;
}}
</style>
"""
