"""
Render a grant application as a PDF for the review team.

Built with ReportLab Platypus so long narrative answers flow across pages
rather than being clipped, which is what a fixed-canvas approach would do.
"""

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# Brand palette, matching the site
NAVY = colors.HexColor("#0D2D5C")
GOLD = colors.HexColor("#D4A017")
FLAME = colors.HexColor("#C8102E")
INK = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#6B7684")
LINE = colors.HexColor("#DCE3EE")
TINT = colors.HexColor("#F2F5FA")

STATUS_COLORS = {
    "New": NAVY,
    "Reviewed": colors.HexColor("#9A6B12"),
    "Approved": colors.HexColor("#2F7A46"),
    "Denied": FLAME,
}

MARGIN = 0.7 * inch


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=17, leading=21, textColor=NAVY, alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=MUTED, spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "section", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8.5, leading=12, textColor=FLAME, spaceBefore=16,
            spaceAfter=6,
        ),
        "label": ParagraphStyle(
            "label", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=7.5, leading=10, textColor=MUTED,
        ),
        "value": ParagraphStyle(
            "value", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, leading=13, textColor=INK,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, leading=13.5, textColor=INK, spaceAfter=9,
        ),
    }


def _escape(value) -> str:
    """Applicant text is untrusted and Paragraph parses markup, so angle
    brackets and ampersands must be neutralised before rendering."""
    if value is None or value == "":
        return "-"
    text = str(value)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.replace("\n", "<br/>")


def build_application_pdf(a) -> BytesIO:
    buf = BytesIO()
    st = _styles()

    doc = BaseDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 0.25 * inch,
        title=f"Grant application: {a.legal_name}",
        author="Pray and Obey Ministries",
    )

    def decorate(canvas, document):
        canvas.saveState()
        # Gold rule across the top, the site's signature device
        canvas.setStrokeColor(GOLD)
        canvas.setLineWidth(2.5)
        y = LETTER[1] - MARGIN + 12
        canvas.line(MARGIN, y, LETTER[0] - MARGIN, y)

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, MARGIN - 6, "Pray and Obey Ministries | Confidential")
        canvas.drawRightString(
            LETTER[0] - MARGIN, MARGIN - 6, f"Page {document.page}"
        )
        canvas.restoreState()

    frame = Frame(
        MARGIN, MARGIN, LETTER[0] - 2 * MARGIN, LETTER[1] - 2 * MARGIN - 6,
        id="body", showBoundary=0,
    )
    doc.addPageTemplates([PageTemplate(id="std", frames=[frame], onPage=decorate)])

    story = []

    # Header
    story.append(Paragraph(_escape(a.legal_name), st["title"]))
    submitted = a.submitted_at.strftime("%B %d, %Y at %H:%M UTC")
    story.append(
        Paragraph(f"Grant application &bull; Submitted {submitted}", st["subtitle"])
    )

    # Status strip
    status_color = STATUS_COLORS.get(a.status, NAVY)
    changed = ""
    if a.status_changed_at:
        changed = a.status_changed_at.strftime("%b %d, %Y")
        if a.status_changed_by:
            changed += f" by {a.status_changed_by}"
    strip = Table(
        [[
            Paragraph(f'<font color="#FFFFFF"><b>{_escape(a.status).upper()}</b></font>',
                      st["value"]),
            Paragraph(
                f'<font size="7.5" color="#6B7684">Requested</font><br/>'
                f'<b>{_escape(a.amount_requested)}</b>', st["value"]),
            Paragraph(
                f'<font size="7.5" color="#6B7684">Status changed</font><br/>'
                f'{_escape(changed) if changed else "-"}', st["value"]),
        ]],
        colWidths=[1.5 * inch, 2.4 * inch, 3.2 * inch],
    )
    strip.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), status_color),
        ("BACKGROUND", (1, 0), (-1, 0), TINT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
    ]))
    story.append(strip)

    def section(title):
        story.append(Paragraph(title.upper(), st["section"]))
        rule = Table([[""]], colWidths=[LETTER[0] - 2 * MARGIN], rowHeights=[1.6])
        rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GOLD)]))
        story.append(rule)
        story.append(Spacer(1, 8))

    def rows(pairs):
        data = [
            [Paragraph(label.upper(), st["label"]),
             Paragraph(_escape(value), st["value"])]
            for label, value in pairs if value not in (None, "")
        ]
        if not data:
            return
        t = Table(data, colWidths=[1.85 * inch, LETTER[0] - 2 * MARGIN - 1.85 * inch])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
        ]))
        story.append(t)

    def block(label, value):
        if not value:
            return
        story.append(KeepTogether([
            Spacer(1, 7),
            Paragraph(label.upper(), st["label"]),
            Spacer(1, 3),
            Paragraph(_escape(value), st["body"]),
        ]))

    # 1. Organization and request
    section("1. Organization and request")
    rows([
        ("Legal name", a.legal_name),
        ("Doing business as", a.dba_name),
        ("Federal EIN", a.ein),
        ("Year founded", a.year_founded),
        ("Website", a.org_website),
        ("Service area", a.service_area),
        ("Contact", a.contact_name),
        ("Email", a.email),
        ("Phone", a.phone),
        ("Mailing address", a.mailing_address),
        ("Organization type", a.org_type),
        ("Amount requested", a.amount_requested),
        ("Total project budget", a.total_project_budget),
        ("Grant period", f"{a.start_date or '?'} to {a.end_date or '?'}"),
    ])
    block("Mission and principal activities", a.mission_activities)
    block("How the ministry shares the Gospel", a.gospel_sharing)
    block("Project summary", a.project_summary)
    block("Who will be served", a.who_served)

    # 2. Mission alignment
    section("2. Mission alignment and Bible distribution")
    rows([
        ("Priorities selected", a.priorities),
        ("Willing to distribute Bibles", a.bible_willingness),
        ("Assistance requested", a.assistance),
    ])
    block("Strongest fit", a.strongest_fit)
    block("Activities, timeline, responsible person", a.activities_timeline)
    block("Use of requested funds", a.funds_use)
    block("Proposed distribution", a.bible_description)
    block("Scripture engagement and follow-up", a.scripture_engagement)

    # 3. Outcomes and finances
    section("3. Outcomes, finances, and certification")
    block("Expected results and measurement", a.expected_results)
    block("Sustainability after the grant", a.sustainability)
    block("Risks and safeguarding", a.risks)

    if a.budget_lines:
        story.append(Spacer(1, 7))
        story.append(Paragraph("BUDGET LINES", st["label"]))
        story.append(Spacer(1, 4))
        data = [["Description", "Total cost", "Requested"]]
        for line in a.budget_lines.split("\n"):
            parts = [p.strip() for p in line.split("|")]
            while len(parts) < 3:
                parts.append("")
            data.append([
                Paragraph(_escape(parts[0]), st["value"]),
                Paragraph(_escape(parts[1].replace("total", "").strip()), st["value"]),
                Paragraph(_escape(parts[2].replace("requested", "").strip()), st["value"]),
            ])
        t = Table(data, colWidths=[3.6 * inch, 1.75 * inch, 1.75 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7.5),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, LINE),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    rows([
        ("Budget total", a.budget_grand_total),
        ("Attachments confirmed ready", a.attachments),
    ])

    if a.files:
        story.append(Spacer(1, 7))
        story.append(Paragraph("UPLOADED DOCUMENTS", st["label"]))
        story.append(Spacer(1, 3))
        listing = "<br/>".join(
            f"&bull; {_escape(f.filename)} ({f.size_label})" for f in a.files
        )
        story.append(Paragraph(listing, st["body"]))
        story.append(Paragraph(
            '<font size="7.5" color="#6B7684">Files are attached to the record in '
            'the portal, not to this PDF.</font>', st["value"]))

    story.append(Spacer(1, 10))
    rows([
        ("Authorized representative", a.authorized_rep),
        ("Title", a.rep_title),
        ("Signature", a.signature),
        ("Certified", "Yes" if a.certified else "No"),
    ])

    if a.reviewer_notes:
        story.append(PageBreak())
        section("Internal review notes")
        story.append(Paragraph(
            '<font size="7.5" color="#6B7684">Not shared with the applicant.</font>',
            st["value"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(_escape(a.reviewer_notes), st["body"]))

    doc.build(story)
    buf.seek(0)
    return buf
