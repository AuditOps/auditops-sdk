from datetime import datetime, timezone
from pathlib import Path
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, Paragraph, Spacer, ListFlowable, 
    ListItem, PageBreak, KeepTogether, Image)
from reportlab.lib.styles import getSampleStyleSheet

from .styles import (
    LABEL_STYLE, VALUE_STYLE, LARGE_VALUE_STYLE, LIST_STYLE, CENTER_STYLE, PASS_COLOR,
    FAIL_COLOR, TABLE_STYLE_HIGHLIGHT_ROW, TABLE_STYLE_HIGHLIGHT_COLUMN,
)

class PDFReportBuilder:

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.page_width, _ = LETTER

    def _format_pct(self, match_count, test_count):
        # Formats percentage with one decimal point (ex. 99.9%) 
        if test_count == 0:
            return f"{count} (0%)"
        pct = (match_count / test_count) * 100
        return f"{match_count} ({pct:.1f}%)"

    def build(self, audit, filename):
        """Generate a PDF audit report."""

        self.audit = audit
        # Sort test results based on risk-rating.
        self.tests = sorted(
            audit.test_results,
            key=lambda t: (t.is_passing, -t.risk_rating)
        )

        self.doc = SimpleDocTemplate(
            filename,
            pagesize=LETTER,
            title=f"{audit.title} Audit Report",
            author="AuditOps",
            subject=f"Audit report for {audit.title}",
        )

        elements = []

        elements.extend(self._build_cover_page())
        elements.extend(self._build_test_summary_page())
        #elements.extend(self._build_test_summary_page())

        self.doc.build(elements)


    def _build_cover_page(self):
        elements = []
        logo = Image(str(Path(__file__).resolve().parent / "assets" / "logo.png"))

        desired_width = 300
        aspect = logo.imageHeight / float(logo.imageWidth)

        logo.drawWidth = desired_width
        logo.drawHeight = desired_width * aspect

        elements.append(logo)
        elements.append(Spacer(1, 24))

        elements.append(
            Paragraph(
                f"{self.audit.title} Audit Report",
                self.styles["Title"],
            )
        )

        elements.append(Spacer(1, 12))

        test_count = len(self.tests)
        failed = sum(not t.is_passing for t in self.tests)
        passed = test_count - failed

        metadata = [
            [Paragraph("Prepared By", LABEL_STYLE), Paragraph("AuditOps", VALUE_STYLE)],

            [Paragraph("Report Date", LABEL_STYLE),
            Paragraph(datetime.now(timezone.utc).strftime("%Y-%m-%d"), VALUE_STYLE)],

            [Paragraph("Tests", LABEL_STYLE), Paragraph(str(test_count), VALUE_STYLE)],

            [Paragraph("Passed", LABEL_STYLE),
            Paragraph(self._format_pct(passed, test_count), VALUE_STYLE)],

            [Paragraph("Failed", LABEL_STYLE),
            Paragraph(self._format_pct(failed, test_count), VALUE_STYLE)],

            [Paragraph("Scope", LABEL_STYLE),
            Paragraph("Coming Soon!", VALUE_STYLE)],
        ]

        table = Table(metadata, colWidths=[200, 150], hAlign="CENTER")

        table.setStyle(TABLE_STYLE_HIGHLIGHT_COLUMN)

        elements.append(table)
        elements.append(PageBreak())

        return elements


    def _build_test_summary_page(self):
        elements = []

        elements.append(
            Paragraph(
                "Test Summary",
                self.styles["Heading1"],
            )
        )

        elements.append(Spacer(1, 12))

        rows = [[
            Paragraph("Test", LABEL_STYLE),
            Paragraph("Result", LABEL_STYLE),
            Paragraph("Risk", LABEL_STYLE),
            Paragraph("Comments", LABEL_STYLE),
        ]]

        for test in self.tests:

            color = PASS_COLOR if test.is_passing else FAIL_COLOR

            rows.append([
                Paragraph(test.test_description, VALUE_STYLE),
                Paragraph(
                    f"<font color='{color}'>{'Pass' if test.is_passing else 'Fail'}</font>",
                    VALUE_STYLE,
                ),
                Paragraph(test.get_risk_rating_str(), VALUE_STYLE),
                Paragraph(test.comments, VALUE_STYLE),
            ])

        table = Table(
            rows,
            colWidths=[220, 60, 70, 140],
        )

        table.setStyle(TABLE_STYLE_HIGHLIGHT_ROW)

        elements.append(table)
        elements.append(PageBreak())

        return elements


    def _build_test_pages(self):
        elements = []

        for test in self.tests:

            elements.append(
                KeepTogether(
                    self._render_test_summary(test)
                )
            )

            elements.append(Spacer(1, 18))

            sample_table = self._render_sample_table(test)

            if sample_table:
                elements.append(
                    KeepTogether(sample_table)
                )
                elements.append(PageBreak())

        return elements