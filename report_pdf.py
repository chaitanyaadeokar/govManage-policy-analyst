"""
report_pdf.py
─────────────
ReportLab PDF generators for govManage.

Professional layout:
  - Dark header band with report-type badge, title & subtitle
  - KPI strip with corrected font sizing (fontSize 14, was 22 — fixes overflow)
  - Coloured top accent line on KPI cells
  - Section headers with left-border accent on a light background pill
  - Page footer with page number and govManage branding on every page

Exports:
    build_compliance_report_pdf(report_data: dict) -> bytes
    build_risk_report_pdf(report_data: dict)       -> bytes
    build_policy_pack_pdf(pack_doc: dict)          -> bytes
    clean_text(val)
"""

from __future__ import annotations

import io
from typing import Any, Dict, List

# ── ReportLab ─────────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    _ok = True
except Exception:
    _ok = False


# ── Colour palette ─────────────────────────────────────────────────────────────

if _ok:
    INDIGO    = rl_colors.HexColor('#4f46e5')
    DARK_BG   = rl_colors.HexColor('#1e293b')
    SLATE     = rl_colors.HexColor('#334155')
    MUTED     = rl_colors.HexColor('#64748b')
    LIGHT_BG  = rl_colors.HexColor('#f8fafc')
    EMERALD   = rl_colors.HexColor('#10b981')
    AMBER     = rl_colors.HexColor('#f59e0b')
    ROSE      = rl_colors.HexColor('#ef4444')
    VIOLET    = rl_colors.HexColor('#7c3aed')
    GRID_CLR  = rl_colors.HexColor('#e2e8f0')
    WHITE     = rl_colors.white
    # Layout constants (in ReportLab points, derived from A4)
    _MARGIN   = 20 * mm                     # left = right margin
    CONTENT_W = A4[0] - 2 * _MARGIN         # ≈ 481.9 pt  ≈ 170 mm


# ── Unicode / Latin-1 sanitiser ───────────────────────────────────────────────

def clean_text(val: Any) -> Any:
    """Recursively strip non-Latin-1 characters so ReportLab doesn't crash."""
    if isinstance(val, str):
        replacements = {
            '‑': '-', '‒': '-', '–': '-', '—': '-',
            '−': '-', '‘': "'", '’': "'", '‚': "'",
            '“': '"', '”': '"', '„': '"', '‟': '"',
            ' ': ' ', ' ': ' ', ' ': ' ',
            '•': '*', '‣': '>', '⁃': '-', '●': '*',
            '…': '...', '·': '.', '→': '->',
            '✓': 'v', '✔': 'v', '✕': 'x', '✖': 'x',
        }
        for old, new in replacements.items():
            val = val.replace(old, new)
        val = val.encode('latin-1', errors='ignore').decode('latin-1')
        return val
    elif isinstance(val, list):
        return [clean_text(i) for i in val]
    elif isinstance(val, dict):
        return {k: clean_text(v) for k, v in val.items()}
    return val


# ── Style factory ─────────────────────────────────────────────────────────────

def _make_styles() -> dict:
    return {
        # ── Header band ────────────────────────────────────────────────────────
        # hb_title kept for backward-compat; _header_band now builds inline styles
        'hb_title': ParagraphStyle(
            'HBTitle', fontName='Helvetica-Bold', fontSize=15,
            textColor=WHITE, spaceAfter=4, leading=22, wordWrap='CJK'),
        'hb_sub': ParagraphStyle(
            'HBSub', fontName='Helvetica', fontSize=8.5,
            textColor=rl_colors.HexColor('#94a3b8'), spaceAfter=0,
            leading=12, wordWrap='CJK'),
        # ── Body text ──────────────────────────────────────────────────────────
        'h2': ParagraphStyle(
            'RPH2', fontName='Helvetica-Bold', fontSize=11,
            textColor=SLATE, spaceBefore=0, spaceAfter=0, wordWrap='CJK'),
        'h3': ParagraphStyle(
            'RPH3', fontName='Helvetica-Bold', fontSize=10,
            textColor=SLATE, spaceBefore=8, spaceAfter=3, wordWrap='CJK'),
        'body': ParagraphStyle(
            'RPBody', fontName='Helvetica', fontSize=9.5,
            textColor=SLATE, spaceAfter=4, leading=14,
            alignment=TA_JUSTIFY, wordWrap='CJK'),
        'bullet': ParagraphStyle(
            'RPBullet', fontName='Helvetica', fontSize=9.5,
            textColor=SLATE, spaceAfter=3, leading=13,
            alignment=TA_JUSTIFY,
            leftIndent=14, bulletIndent=0, wordWrap='CJK'),
        # ── Table cells ────────────────────────────────────────────────────────
        'th': ParagraphStyle(
            'RPTH', fontName='Helvetica-Bold', fontSize=9,
            textColor=WHITE, leading=11, wordWrap='CJK'),
        'td': ParagraphStyle(
            'RPTD', fontName='Helvetica', fontSize=8.5,
            textColor=SLATE, leading=11, wordWrap='CJK'),
        'td_bold': ParagraphStyle(
            'RPTDBold', fontName='Helvetica-Bold', fontSize=8.5,
            textColor=SLATE, leading=11, wordWrap='CJK'),
        # ── KPI strip ──────────────────────────────────────────────────────────
        # FIXED: was fontSize=22 → overflowed "Developing"/"2026-06-03" in 42 mm cells.
        # At 14pt Helvetica-Bold, "Developing" ≈ 28 mm — safe in a ~40 mm content cell.
        'score': ParagraphStyle(
            'RPScore', fontName='Helvetica-Bold', fontSize=14,
            textColor=INDIGO, spaceAfter=2, alignment=TA_CENTER, wordWrap='CJK'),
        'score_label': ParagraphStyle(
            'RPScoreLabel', fontName='Helvetica', fontSize=8,
            textColor=MUTED, spaceAfter=0, alignment=TA_CENTER, wordWrap='CJK'),
    }


# ── Document template ─────────────────────────────────────────────────────────

def _doc(buf: io.BytesIO) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=_MARGIN, rightMargin=_MARGIN,
        topMargin=35 * mm,      # increased further for larger top-left logo
        bottomMargin=22 * mm,   # extra space for the page-footer band
    )


# ── Page-footer callback factory ──────────────────────────────────────────────

def _make_footer(accent=None):
    """
    Return an onPage callback that draws branding + page number at page bottom.
    Captured colour avoids a module-level reference before _ok is set.
    """
    _accent = accent  # captured in closure

    def _draw(canvas, doc):
        canvas.saveState()
        w = A4[0]
        h = A4[1]
        
        # --- Logo at Top Left ---
        try:
            # Make the logo larger and move it more to the top-left corner
            logo_width = 45 * mm
            logo_height = 20 * mm
            logo_x = 12 * mm       # Less than standard _MARGIN (20mm) to push it left
            logo_y = h - 28 * mm   # Move it up 
            canvas.drawImage("Logo.png", logo_x, logo_y, width=logo_width, height=logo_height, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass # fail gracefully if Logo.png is not found or invalid

        y = 8 * mm
        # Rule
        canvas.setStrokeColor(GRID_CLR)
        canvas.setLineWidth(0.4)
        canvas.line(_MARGIN, y + 5 * mm, w - _MARGIN, y + 5 * mm)
        # Branding (left) + page number (right)
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(_MARGIN, y, 'govManage GRC Platform  |  Confidential')
        canvas.drawRightString(w - _MARGIN, y, f'Page {doc.page}')
        
        # AI generated remark at the very bottom
        canvas.setFont('Helvetica-Oblique', 7)
        canvas.drawCentredString(w / 2, y - 4 * mm, 'AI generated remark')
        
        canvas.restoreState()

    return _draw


# ── Layout helpers ────────────────────────────────────────────────────────────

def _header_band(
    story: list,
    report_type: str,
    title: str,
    subtitle: str,
    s: dict,
    accent=None,
):
    """
    Render a full-width dark header band with a two-tier title layout.

    Long titles such as "Compliance Report - Sovereign AI Security Policy"
    are split on the first dash separator into:
      • tier 1  — report-type label  (Helvetica-Bold 16 pt, white)
      • tier 2  — policy/pack name   (Helvetica 11 pt, muted slate #cbd5e1)

    When no separator is found (e.g. a bare policy name) the title is
    displayed as a single line at 15 pt bold — it is already short enough.

    Table rows:
      row 0  — small ALL-CAPS badge in accent colour
      row 1  — two-tier (or single) title paragraph
      row 2  — subtitle / meta line (muted grey, 8.5 pt)
    """
    accent = accent or INDIGO

    badge_style = ParagraphStyle(
        f'HBBadge{id(accent)}', fontName='Helvetica-Bold', fontSize=8,
        textColor=accent, spaceAfter=0, wordWrap='CJK')

    def _xe(t: str) -> str:
        """Minimal XML-entity escape for ReportLab Paragraph content."""
        return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # ── Detect two-tier separator: ' - ', ' -- ', em-dash, en-dash ────────────
    tier1: str | None = None
    tier2: str = title
    for sep in (' - ', ' -- ', ' — ', ' – ', '—', '–'):
        idx = title.find(sep)
        if idx > 0:
            tier1 = title[:idx].strip()
            tier2 = title[idx + len(sep):].strip()
            break

    if tier1:
        # Two-tier: "Report Type" large + "Policy Name" smaller, both on DARK_BG
        title_xml = (
            f'<font name="Helvetica-Bold" size="16" color="white">{_xe(tier1)}</font>'
            '<br/>'
            f'<font name="Helvetica" size="11" color="#cbd5e1">{_xe(tier2)}</font>'
        )
        title_leading = 26   # accommodates 16 pt + br gap + 11 pt
    else:
        # Single-tier: bare policy name or short title
        title_xml = (
            f'<font name="Helvetica-Bold" size="15" color="white">{_xe(tier2)}</font>'
        )
        title_leading = 22

    title_para_style = ParagraphStyle(
        f'HBTitleDyn{id(title)}',
        fontName='Helvetica', fontSize=16,   # base; actual size set by inline tags
        textColor=WHITE, leading=title_leading,
        spaceAfter=0, wordWrap='CJK',
    )

    tbl = Table(
        [
            [Paragraph(report_type.upper(), badge_style)],
            [Paragraph(title_xml, title_para_style)],
            [Paragraph(subtitle, s['hb_sub'])],
        ],
        colWidths=[CONTENT_W],
    )
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), DARK_BG),
        ('LEFTPADDING',   (0, 0), (-1, -1), 20),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 20),
        # Row 0: badge
        ('TOPPADDING',    (0, 0), (0, 0), 16),
        ('BOTTOMPADDING', (0, 0), (0, 0),  4),
        # Row 1: title (generous bottom pad for the two-tier case)
        ('TOPPADDING',    (0, 1), (0, 1),  4),
        ('BOTTOMPADDING', (0, 1), (0, 1), 12),
        # Row 2: subtitle
        ('TOPPADDING',    (0, 2), (0, 2),  4),
        ('BOTTOMPADDING', (0, 2), (0, 2), 18),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6 * mm))


def _kpi_table(story: list, kpis: List[Dict[str, Any]], s: dict, accent=None):
    """
    Render a row of N equal-width KPI metric boxes.

    Overflow fix:
      font size reduced from 22 → 14 pt.
      At 14pt Helvetica-Bold the widest expected values
      ('Developing', '2026-06-03') are ~28 mm — well within each cell.
    """
    accent = accent or INDIGO
    n      = len(kpis)
    col_w  = CONTENT_W / n

    row = []
    for kpi in kpis:
        cell = [
            Paragraph(str(kpi['value']), s['score']),
            Spacer(1, 1),
            Paragraph(kpi['label'], s['score_label']),
        ]
        row.append(cell)

    tbl = Table([row], colWidths=[col_w] * n)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), LIGHT_BG),
        ('BOX',           (0, 0), (-1, -1), 0.4, GRID_CLR),
        ('INNERGRID',     (0, 0), (-1, -1), 0.4, GRID_CLR),
        ('LINEABOVE',     (0, 0), (-1,  0), 2.5, accent),  # coloured top stripe
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING',   (0, 0), (-1, -1),  4),
        ('RIGHTPADDING',  (0, 0), (-1, -1),  4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 5 * mm))


def _section_header(story: list, title: str, s: dict, accent=None):
    """Section heading with a coloured 3 pt left-border on a light background pill."""
    accent = accent or INDIGO
    tbl = Table([[Paragraph(title, s['h2'])]], colWidths=[CONTENT_W])
    tbl.setStyle(TableStyle([
        ('LINEBEFORE',    (0, 0), (0, -1), 3,  accent),
        ('BACKGROUND',    (0, 0), (-1, -1), LIGHT_BG),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1),  6),
        ('TOPPADDING',    (0, 0), (-1, -1),  6),
        ('BOTTOMPADDING', (0, 0), (-1, -1),  6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 3 * mm))


def _bullet_list(story: list, items: List[str], s: dict, prefix: str = '*'):
    for item in items:
        story.append(Paragraph(f'{prefix}  {item}', s['bullet']))


def _divider(story: list, color=None):
    story.append(Spacer(1, 2 * mm))
    story.append(HRFlowable(
        width='100%', thickness=0.5,
        color=color or GRID_CLR, spaceAfter=3 * mm))


# ── Score / severity colour helpers ───────────────────────────────────────────

def _score_color(score: int):
    return EMERALD if score >= 80 else AMBER if score >= 60 else ROSE


def _severity_color(sev: str):
    s = sev.strip().lower()
    return ROSE if s == 'high' else AMBER if s == 'medium' else EMERALD


# ── 1. Compliance Report PDF ──────────────────────────────────────────────────

def build_compliance_report_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Generate a professional A4 PDF for a compliance gap report.
    report_data: JSON dict returned by /api/reports/compliance.
    Returns raw PDF bytes, or b"" if reportlab is unavailable.
    """
    if not _ok:
        return b""

    report_data = clean_text(report_data)
    s   = _make_styles()
    buf = io.BytesIO()
    story: list = []

    title    = report_data.get('report_title', 'Compliance Gap Report')
    gen_at   = report_data.get('generated_at', '')
    fw_ids   = ', '.join(report_data.get('framework_ids', []))
    overall  = report_data.get('compliance_scores', {}).get('overall', 0)
    maturity = report_data.get('maturity_level', 'N/A')
    next_rev = report_data.get('next_review_date', 'N/A')
    gaps_cnt = len(report_data.get('critical_gaps', []))

    # ── Dark header band ──────────────────────────────────────────────────────
    subtitle = f"Generated: {gen_at}  |  Frameworks: {fw_ids or 'N/A'}"
    _header_band(story, 'Compliance Gap Report', title, subtitle, s, EMERALD)

    # ── KPI strip ─────────────────────────────────────────────────────────────
    _kpi_table(story, [
        {'value': f"{overall}%", 'label': 'Overall Score'},
        {'value': maturity,      'label': 'Maturity Level'},
        {'value': next_rev,      'label': 'Next Review'},
        {'value': str(gaps_cnt), 'label': 'Critical Gaps'},
    ], s, accent=EMERALD)

    # ── 1. Executive Summary ──────────────────────────────────────────────────
    _section_header(story, '1. Executive Summary', s, INDIGO)
    story.append(Paragraph(report_data.get('executive_summary', ''), s['body']))
    story.append(Spacer(1, 3 * mm))

    # ── 2. Framework Breakdown ────────────────────────────────────────────────
    fw_scores = report_data.get('compliance_scores', {}).get('by_framework', [])
    if fw_scores:
        _section_header(story, '2. Framework Compliance Breakdown', s, EMERALD)
        tdata = [[
            Paragraph('Framework', s['th']),
            Paragraph('Score',     s['th']),
            Paragraph('Status',    s['th']),
        ]]
        for fw in fw_scores:
            tdata.append([
                Paragraph(fw.get('framework', ''), s['td_bold']),
                Paragraph(f"{fw.get('score', 0)}%", s['td']),
                Paragraph(fw.get('status', 'N/A'), s['td']),
            ])
        tbl = Table(tdata, colWidths=[90 * mm, 30 * mm, 50 * mm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), EMERALD),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, rl_colors.HexColor('#f0fdf4')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 4 * mm))

    # ── 3. Key Findings ───────────────────────────────────────────────────────
    findings = report_data.get('key_findings', [])
    if findings:
        _section_header(story, '3. Key Findings', s, INDIGO)
        _bullet_list(story, findings, s)
        story.append(Spacer(1, 2 * mm))

    # ── 4. Critical Gaps ──────────────────────────────────────────────────────
    gaps = report_data.get('critical_gaps', [])
    if gaps:
        _section_header(story, '4. Critical Gaps', s, ROSE)
        _bullet_list(story, gaps, s)
        story.append(Spacer(1, 2 * mm))

    # ── 5. Recommendations ────────────────────────────────────────────────────
    recs = report_data.get('recommendations', [])
    if recs:
        _section_header(story, '5. Recommendations', s, VIOLET)
        _bullet_list(story, recs, s)
        story.append(Spacer(1, 2 * mm))

    # ── 6. Action Plan ────────────────────────────────────────────────────────
    actions = report_data.get('action_plan', [])
    if actions:
        _section_header(story, '6. Action Plan', s, AMBER)
        adata = [[
            Paragraph('Priority', s['th']),
            Paragraph('Action',   s['th']),
            Paragraph('Timeline', s['th']),
            Paragraph('Owner',    s['th']),
        ]]
        for a in actions:
            adata.append([
                Paragraph(a.get('priority', ''), s['td_bold']),
                Paragraph(a.get('action',   ''), s['td']),
                Paragraph(a.get('timeline', ''), s['td']),
                Paragraph(a.get('owner',    ''), s['td']),
            ])
        atbl = Table(adata, colWidths=[22 * mm, 90 * mm, 30 * mm, 28 * mm])
        atbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), AMBER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, rl_colors.HexColor('#fffbeb')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(atbl)

    footer = _make_footer(EMERALD)
    doc = _doc(buf)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


# ── 2. Risk Report PDF ────────────────────────────────────────────────────────

def build_risk_report_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Generate a professional A4 PDF for a risk assessment report.
    report_data: JSON dict returned by /api/reports/risk.
    Returns raw PDF bytes, or b"" if reportlab is unavailable.
    """
    if not _ok:
        return b""

    report_data = clean_text(report_data)
    s   = _make_styles()
    buf = io.BytesIO()
    story: list = []

    title      = report_data.get('report_title', 'Risk Assessment Report')
    gen_at     = report_data.get('generated_at', '')
    posture    = report_data.get('risk_posture', 'N/A')
    risk_score = report_data.get('overall_risk_score', 0)

    risk_items = report_data.get('risk_items', [])
    high_cnt   = sum(1 for r in risk_items if r.get('severity', '').lower() == 'high')
    med_cnt    = sum(1 for r in risk_items if r.get('severity', '').lower() == 'medium')
    low_cnt    = sum(1 for r in risk_items if r.get('severity', '').lower() == 'low')

    # ── Dark header band ──────────────────────────────────────────────────────
    subtitle = f"Generated: {gen_at}  |  Posture: {posture}  |  Score: {risk_score}/100"
    _header_band(story, 'Risk Assessment Report', title, subtitle, s, ROSE)

    # ── KPI strip ─────────────────────────────────────────────────────────────
    _kpi_table(story, [
        {'value': f"{risk_score}/100",    'label': 'Risk Score'},
        {'value': posture,                'label': 'Posture'},
        {'value': str(high_cnt),          'label': 'High Risks'},
        {'value': str(med_cnt + low_cnt), 'label': 'Med / Low'},
    ], s, accent=ROSE)

    # ── 1. Executive Summary ──────────────────────────────────────────────────
    _section_header(story, '1. Executive Summary', s, INDIGO)
    story.append(Paragraph(report_data.get('executive_summary', ''), s['body']))
    story.append(Spacer(1, 3 * mm))

    # ── 2. Key Findings ───────────────────────────────────────────────────────
    findings = report_data.get('key_findings', [])
    if findings:
        _section_header(story, '2. Key Findings', s, INDIGO)
        _bullet_list(story, findings, s)
        story.append(Spacer(1, 2 * mm))

    # ── 3. High-Priority Risks ────────────────────────────────────────────────
    hi_risks = report_data.get('high_priority_risks', [])
    if hi_risks:
        _section_header(story, '3. High-Priority Risks', s, ROSE)
        _bullet_list(story, hi_risks, s)
        story.append(Spacer(1, 2 * mm))

    # ── 4. Risk Register ──────────────────────────────────────────────────────
    if risk_items:
        _section_header(story, '4. Risk Register', s, AMBER)
        rdata = [[
            Paragraph('Risk ID',    s['th']),
            Paragraph('Title',      s['th']),
            Paragraph('Type',       s['th']),
            Paragraph('Severity',   s['th']),
            Paragraph('Mitigation', s['th']),
        ]]
        for r in risk_items:
            rdata.append([
                Paragraph(r.get('risk_id',    ''), s['td_bold']),
                Paragraph(r.get('title',      ''), s['td']),
                Paragraph(r.get('risk_type',  ''), s['td']),
                Paragraph(r.get('severity',   ''), s['td']),
                Paragraph(r.get('mitigation', ''), s['td']),
            ])
        rtbl = Table(rdata, colWidths=[18 * mm, 35 * mm, 22 * mm, 18 * mm, 77 * mm])
        rtbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), AMBER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, rl_colors.HexColor('#fffbeb')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(rtbl)
        story.append(Spacer(1, 4 * mm))

    # ── 5. Risk Treatment Plan ────────────────────────────────────────────────
    treatment_plan = report_data.get('risk_treatment_plan', [])
    if treatment_plan:
        _section_header(story, '5. Risk Treatment Plan', s, VIOLET)
        tdata = [[
            Paragraph('Risk ID',   s['th']),
            Paragraph('Risk',      s['th']),
            Paragraph('Treatment', s['th']),
            Paragraph('Action',    s['th']),
            Paragraph('Timeline',  s['th']),
        ]]
        for t in treatment_plan:
            tdata.append([
                Paragraph(t.get('risk_id',   ''), s['td_bold']),
                Paragraph(t.get('risk',      ''), s['td']),
                Paragraph(t.get('treatment', ''), s['td']),
                Paragraph(t.get('action',    ''), s['td']),
                Paragraph(t.get('timeline',  ''), s['td']),
            ])
        ttbl = Table(tdata, colWidths=[18 * mm, 35 * mm, 22 * mm, 65 * mm, 30 * mm])
        ttbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), VIOLET),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, rl_colors.HexColor('#f5f3ff')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(ttbl)
        story.append(Spacer(1, 4 * mm))

    # ── 6. Residual Risks ─────────────────────────────────────────────────────
    residuals = report_data.get('residual_risks', [])
    if residuals:
        _section_header(story, '6. Residual Risks', s, ROSE)
        _bullet_list(story, residuals, s)
        story.append(Spacer(1, 2 * mm))

    # ── 7. Recommendations ────────────────────────────────────────────────────
    recs = report_data.get('recommendations', [])
    if recs:
        _section_header(story, '7. Recommendations', s, INDIGO)
        _bullet_list(story, recs, s)
        story.append(Spacer(1, 2 * mm))

    # ── 8. Governance Actions ─────────────────────────────────────────────────
    gov_actions = report_data.get('governance_actions', [])
    if gov_actions:
        _section_header(story, '8. Governance Actions', s, EMERALD)
        gdata = [[
            Paragraph('Action',   s['th']),
            Paragraph('Owner',    s['th']),
            Paragraph('Due Date', s['th']),
        ]]
        for g in gov_actions:
            gdata.append([
                Paragraph(g.get('action',   ''), s['td']),
                Paragraph(g.get('owner',    ''), s['td_bold']),
                Paragraph(g.get('due_date', ''), s['td']),
            ])
        gtbl = Table(gdata, colWidths=[110 * mm, 35 * mm, 25 * mm])
        gtbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), EMERALD),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, rl_colors.HexColor('#f0fdf4')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(gtbl)

    footer = _make_footer(ROSE)
    doc = _doc(buf)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


# ── 3. Policy Pack PDF ────────────────────────────────────────────────────────

def build_policy_pack_pdf(pack_doc: Dict[str, Any]) -> bytes:
    """
    Generate a professional A4 PDF for a policy pack document.
    Uses the same layout language (header band, KPI strip, section headers,
    page footer) as the compliance and risk report PDFs.
    pack_doc: the MongoDB document as stored by db.add_policy_pack().
    Returns raw PDF bytes, or b"" if reportlab is unavailable.
    """
    if not _ok:
        return b""

    pack_doc = clean_text(pack_doc)
    s   = _make_styles()
    buf = io.BytesIO()
    story: list = []

    policy   = pack_doc.get('policy', {})
    pack_id  = pack_doc.get('pack_id', '')
    sector   = pack_doc.get('sector', '—')
    country  = pack_doc.get('country', 'Global')
    risk_lvl = pack_doc.get('risk_level', '—')

    # Compliance scores embedded in the policy sub-document
    scores       = policy.get('compliance_scores', {})
    completeness = scores.get('policy_completeness', 100)
    risk_cov     = scores.get('risk_coverage', 100)
    comp_ready   = scores.get('compliance_readiness', 100)

    title    = policy.get('name', pack_doc.get('topic', 'Policy Pack'))
    subtitle = f"Sector: {sector}  |  Country: {country}  |  Risk Level: {risk_lvl}  |  ID: {pack_id}"

    # ── Dark header band ──────────────────────────────────────────────────────
    _header_band(story, 'Policy Document', title, subtitle, s, INDIGO)

    # ── KPI strip ─────────────────────────────────────────────────────────────
    _kpi_table(story, [
        {'value': f"{completeness}%", 'label': 'Policy Complete'},
        {'value': f"{risk_cov}%",     'label': 'Risk Coverage'},
        {'value': f"{comp_ready}%",   'label': 'Compliance Ready'},
        {'value': risk_lvl,           'label': 'Risk Level'},
    ], s, accent=INDIGO)

    # Procedure sub-header style (not in _make_styles to keep it lean)
    proc_title_s = ParagraphStyle(
        'RPProcTitle', fontName='Helvetica-Bold', fontSize=10,
        textColor=SLATE, spaceBefore=5, spaceAfter=3, wordWrap='CJK')

    # ── 1. Objective ──────────────────────────────────────────────────────────
    _section_header(story, '1. Objective', s, INDIGO)
    story.append(Paragraph(policy.get('objective', ''), s['body']))
    story.append(Spacer(1, 3 * mm))

    # ── 2. Scope ──────────────────────────────────────────────────────────────
    _section_header(story, '2. Scope', s, INDIGO)
    story.append(Paragraph(policy.get('scope', ''), s['body']))
    story.append(Spacer(1, 3 * mm))

    # ── 3. Policy Statements ──────────────────────────────────────────────────
    stmts = policy.get('policy_statements', [])
    if stmts:
        _section_header(story, '3. Policy Statements', s, EMERALD)
        for stmt in stmts:
            story.append(Paragraph(f'*  {stmt}', s['bullet']))
        story.append(Spacer(1, 2 * mm))

    # ── 4. Procedures ─────────────────────────────────────────────────────────
    procs = policy.get('procedures', [])
    if procs:
        _section_header(story, '4. Procedures', s, VIOLET)
        for proc in procs:
            story.append(Paragraph(proc.get('title', ''), proc_title_s))
            for j, step in enumerate(proc.get('steps', []), 1):
                story.append(Paragraph(f'{j}.  {step}', s['bullet']))
            story.append(Spacer(1, 2 * mm))

    # ── 5. Enforcement ────────────────────────────────────────────────────────
    enforcement = policy.get('enforcement', '')
    if enforcement:
        _section_header(story, '5. Enforcement', s, ROSE)
        story.append(Paragraph(enforcement, s['body']))
        story.append(Spacer(1, 3 * mm))

    # ── 6. Review Cycle ───────────────────────────────────────────────────────
    review = policy.get('review_cycle', '')
    if review:
        _section_header(story, '6. Review Cycle', s, AMBER)
        story.append(Paragraph(review, s['body']))
        story.append(Spacer(1, 3 * mm))

    # ── 7. Governance Structure ───────────────────────────────────────────────
    gov = policy.get('governance_structure', [])
    if gov:
        _section_header(story, '7. Governance Structure', s, INDIGO)
        gdata = [[
            Paragraph('Role',           s['th']),
            Paragraph('Responsibility', s['th']),
        ]]
        for g in gov:
            gdata.append([
                Paragraph(g.get('role',           ''), s['td_bold']),
                Paragraph(g.get('responsibility', ''), s['td']),
            ])
        gtbl = Table(gdata, colWidths=[55 * mm, 115 * mm])
        gtbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), INDIGO),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(gtbl)
        story.append(Spacer(1, 4 * mm))

    # ── 8. Compliance Control Matrix ──────────────────────────────────────────
    matrix = pack_doc.get('compliance_matrix', [])
    if matrix:
        _section_header(story, '8. Compliance Control Matrix', s, EMERALD)
        mdata = [[
            Paragraph('Framework',  s['th']),
            Paragraph('Control ID', s['th']),
            Paragraph('Title',      s['th']),
            Paragraph('Coverage',   s['th']),
        ]]
        for c in matrix:
            mdata.append([
                Paragraph(c.get('framework_id', ''), s['td_bold']),
                Paragraph(c.get('control_id',   ''), s['td']),
                Paragraph(c.get('title',        ''), s['td']),
                Paragraph(c.get('coverage',     ''), s['td']),
            ])
        mtbl = Table(mdata, colWidths=[32 * mm, 22 * mm, 88 * mm, 28 * mm])
        mtbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), EMERALD),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, rl_colors.HexColor('#f0fdf4')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(mtbl)
        story.append(Spacer(1, 4 * mm))

    # ── 9. Risk Mitigation Mapping ────────────────────────────────────────────
    risks = pack_doc.get('risk_mapping', [])
    if risks:
        _section_header(story, '9. Risk Mitigation Mapping', s, AMBER)
        rdata = [[
            Paragraph('Risk ID',   s['th']),
            Paragraph('Risk Type', s['th']),
            Paragraph('Mitigation',s['th']),
            Paragraph('Severity',  s['th']),
        ]]
        for r in risks:
            rdata.append([
                Paragraph(r.get('risk_id',    ''), s['td_bold']),
                Paragraph(r.get('risk_type',  ''), s['td']),
                Paragraph(r.get('mitigation', ''), s['td']),
                Paragraph(r.get('severity',   ''), s['td']),
            ])
        rtbl = Table(rdata, colWidths=[22 * mm, 28 * mm, 98 * mm, 22 * mm])
        rtbl.setStyle(TableStyle([
            ('BACKGROUND',     (0, 0), (-1,  0), AMBER),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, rl_colors.HexColor('#fffbeb')]),
            ('GRID',           (0, 0), (-1, -1), 0.4, GRID_CLR),
            ('VALIGN',         (0, 0), (-1, -1), 'TOP'),
            ('PADDING',        (0, 0), (-1, -1), 5),
        ]))
        story.append(rtbl)

    footer = _make_footer(INDIGO)
    doc = _doc(buf)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


# ── 4. Markdown Policy PDF ────────────────────────────────────────────────────────

def build_markdown_policy_pdf(policy_doc: Dict[str, Any]) -> bytes:
    """
    Generate a professional A4 PDF for a raw markdown policy document.
    """
    if not _ok:
        return b""

    policy_doc = clean_text(policy_doc)
    s   = _make_styles()
    buf = io.BytesIO()
    story: list = []

    title    = policy_doc.get('title') or policy_doc.get('name') or "Policy Document"
    sector   = policy_doc.get('sector', 'General')
    date_str = policy_doc.get('created_at', '')[:10]
    policy_id = policy_doc.get('policy_id') or policy_doc.get('document_id') or ''
    subtitle = f"Sector: {sector}  |  Date: {date_str}  |  ID: {policy_id}"

    _header_band(story, 'Policy Document', title, subtitle, s, INDIGO)

    lines = policy_doc.get("content", "").split("\n")
    import re
    
    table_lines = []
    
    def flush_table():
        if not table_lines:
            return
        
        # Parse table_lines into a ReportLab Table
        data = []
        for r_idx, r_line in enumerate(table_lines):
            # Skip separator line like |---|---|
            if re.match(r'^\|[\s\-\|:]+\|$', r_line.strip()):
                continue
            
            # Extract cells
            cells = [c.strip() for c in r_line.strip().strip('|').split('|')]
            row_data = []
            for cell in cells:
                # convert **bold**
                cell = cell.replace("<br>", "<br/>")
                cell = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', cell)
                
                # if it's the very first line parsed, it's the header
                if len(data) == 0:
                    row_data.append(Paragraph(cell, s['th']))
                else:
                    row_data.append(Paragraph(cell, s['td']))
            if row_data:
                data.append(row_data)
        
        if data:
            cols = max(len(r) for r in data)
            padded_data = []
            for row in data:
                if len(row) < cols:
                    style = s['th'] if len(padded_data) == 0 else s['td']
                    row = row + [Paragraph("", style)] * (cols - len(row))
                padded_data.append(row)
                
            colWidths = [CONTENT_W / cols] * cols if cols > 0 else None
            
            tbl = Table(padded_data, colWidths=colWidths)
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), INDIGO),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
                ('GRID', (0, 0), (-1, -1), 0.4, GRID_CLR),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 4 * mm))
        
        table_lines.clear()

    for line in lines:
        stripped = line.strip()
        
        if stripped.startswith("|") and stripped.endswith("|") and len(stripped) > 2:
            table_lines.append(stripped)
            continue
        else:
            flush_table()

        if line.startswith("# "):
            story.append(Paragraph(line[2:], s['h2']))
            story.append(Spacer(1, 3 * mm))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], s['h3']))
            story.append(Spacer(1, 2 * mm))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], s['h3']))
            story.append(Spacer(1, 2 * mm))
        elif stripped == "---" or stripped == "***":
            story.append(Spacer(1, 2 * mm))
            story.append(HRFlowable(width='100%', thickness=0.5, color=GRID_CLR, spaceAfter=3 * mm))
        elif line.strip() == "":
            story.append(Spacer(1, 10))
        else:
            # Fix <br> tags and bolding for ReportLab
            text = line.replace("<br>", "<br/>")
            text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
            
            # Extract bullet
            if re.match(r'^[-*]\s+', text):
                text = re.sub(r'^[-*]\s+', '', text)
                story.append(Paragraph(f'*  {text}', s['bullet']))
            else:
                story.append(Paragraph(text, s['body']))
    
    flush_table()

    footer = _make_footer(INDIGO)
    doc = _doc(buf)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
