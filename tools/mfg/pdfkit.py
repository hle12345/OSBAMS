"""Small reportlab helpers for the text-heavy PDFs."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

SS = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=SS["Heading1"], fontSize=16, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=SS["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=4)
BODY = ParagraphStyle("B", parent=SS["BodyText"], fontSize=8.8, leading=11.5)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=7.4, leading=9.2)
WARN = ParagraphStyle("W", parent=BODY, textColor=colors.HexColor("#a00000"), backColor=colors.HexColor("#fdecec"),
                      borderPadding=4, spaceBefore=4, spaceAfter=6)
BAD = colors.HexColor("#fdecec")
OK = colors.HexColor("#e9f7ec")
HEAD = colors.HexColor("#dfe6f0")


def P(t, st=BODY):
    return Paragraph(t, st)


def table(rows, widths=None, header=True, font=7.6, shade=None):
    data = [[Paragraph(str(c), ParagraphStyle("c", parent=BODY, fontSize=font, leading=font + 2)) for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.3, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), HEAD))
    for (r, col) in (shade or []):
        st.append(("BACKGROUND", (0, r), (-1, r), col))
    t.setStyle(TableStyle(st))
    return t


def build(path, story, title, landscape_mode=False, footer="OSBAMS Rev.2 controller PCB — NOT RELEASED FOR PRODUCTION"):
    size = landscape(A4) if landscape_mode else A4
    def foot(c, d):
        c.saveState(); c.setFont("Helvetica", 6.5); c.setFillColor(colors.HexColor("#a00000"))
        c.drawString(15 * mm, 8 * mm, f"{title} | {footer} | page {d.page}")
        c.restoreState()
    doc = SimpleDocTemplate(path, pagesize=size, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=14 * mm,
                            bottomMargin=16 * mm, title=title, author="OSBAMS")
    doc.build(story, onFirstPage=foot, onLaterPages=foot)
