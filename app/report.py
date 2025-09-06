import os
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

def build_pdf_report(job_id, results, storage):
    brand = os.getenv("BRAND_NAME", "AI Discoverability Scanner")
    contact = os.getenv("CONTACT_EMAIL", "")
    pdf_local = f"./jobs/{job_id}/report.pdf"
    os.makedirs(os.path.dirname(pdf_local), exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=11, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="SectionHeader", fontSize=14, leading=18, spaceAfter=6))
    styles.add(ParagraphStyle(name="NormalTight", fontSize=10, leading=12))

    story = []
    story.append(Paragraph(f"{brand} — AI Discoverability Report", styles['Title']))
    story.append(Paragraph(f"Target: {results['root']} &nbsp;&nbsp; Duration: {results['duration_sec']}s", styles['Normal']))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Scorecard", styles['SectionHeader']))
    s = results["scores"]
    table_data = [
        ["Category", "Score"],
        ["A. Crawlability", s["A_crawlability"]],
        ["B. Structured Data", s["B_structured_data"]],
        ["C. Answerability", s["C_answerability"]],
        ["D. Authority", s["D_authority"]],
        ["E. Technical", s["E_technical"]],
        ["F. Agent Endpoints", s["F_agent_endpoints"]],
        ["Overall", s["overall"]],
    ]
    tbl = Table(table_data, colWidths=[3.2*72, 1.2*72])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.HexColor("#e8eef9")),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),0.25, colors.grey),
        ('ALIGN',(1,1),(-1,-1),'CENTER')
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Pages Scanned (examples)", styles['SectionHeader']))
    for pg in results["pages"][:5]:
        story.append(Paragraph(f"<b>{pg['title'] or pg['url']}</b><br/>{pg['url']}", styles['NormalTight']))
        if pg['h1']:
            story.append(Paragraph(f"H1: {', '.join(pg['h1'][:3])}", styles['Small']))
        if pg['h2']:
            story.append(Paragraph(f"H2: {', '.join(pg['h2'][:5])}", styles['Small']))
        if pg['json_ld_types']:
            story.append(Paragraph(f"JSON-LD types: {', '.join([str(x) for x in pg['json_ld_types']])}", styles['Small']))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Top Recommendations", styles['SectionHeader']))
    recs = []
    if not results["robots_present"]:
        recs.append("Add robots.txt and link sitemap.xml; ensure GPTBot/CCBot are allowed or explicitly configured.")
    if results["scores"]["B_structured_data"] == 0:
        recs.append("Add JSON-LD schema (Organization, Service/Product, Article, FAQPage) aligned with visible content.")
    if results["answerability_ratio"] < 0.2:
        recs.append("Use question-style headings (H2) and concise 40–120 word answer blocks near the top of pages.")
    if results["scores"]["D_authority"] == 0:
        recs.append("Add visible 'About/Contact/Privacy/Terms' and author bios on posts for stronger authority signals.")
    if not recs:
        recs.append("Great foundation. Expand schema coverage and consider adding a Q&A/FAQ section on key pages.")

    for r in recs:
        story.append(Paragraph(f"• {r}", styles['NormalTight']))

    if contact:
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Contact: {contact}", styles['Small']))

    doc = SimpleDocTemplate(pdf_local, pagesize=LETTER, leftMargin=0.7*72, rightMargin=0.7*72, topMargin=0.7*72, bottomMargin=0.7*72)
    doc.build(story)
    return pdf_local
