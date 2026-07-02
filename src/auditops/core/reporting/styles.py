from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import TableStyle

# Base styles
BASE_STYLES = getSampleStyleSheet()

# Paragraph styles
LABEL_STYLE = ParagraphStyle(
    name="Label",
    fontName="Helvetica-Bold",
    fontSize=9,
)

VALUE_STYLE = ParagraphStyle(
    name="Value",
    fontName="Helvetica",
    fontSize=9,
)

LARGE_VALUE_STYLE = ParagraphStyle(
    name="LargeValue",
    parent=VALUE_STYLE,
    fontSize=11,
    leading=15,
    spaceAfter=2,
)

LIST_STYLE = ParagraphStyle(
    name="List",
    parent=VALUE_STYLE,
    spaceAfter=6,
)

CENTER_STYLE = ParagraphStyle(
    name="Center",
    parent=VALUE_STYLE,
    alignment=1,
)

# Colors
HEADER_BG = colors.lightgrey
PASS_COLOR = "green"
FAIL_COLOR = "red"

# Table styles
TABLE_STYLE_HIGHLIGHT_ROW = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
])

TABLE_STYLE_HIGHLIGHT_COLUMN = TableStyle([
    ("BACKGROUND", (0, 0), (0, -1), HEADER_BG),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ("PADDING", (0, 0), (-1, -1), 6),
])