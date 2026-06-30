from datetime import datetime, timezone
from pathlib import Path
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, Paragraph, Spacer, PageBreak, KeepTogether, Image)
from reportlab.lib.styles import getSampleStyleSheet
from .styles import (LABEL_STYLE, VALUE_STYLE, LIST_STYLE, CENTER_STYLE, PASS_COLOR,
    FAIL_COLOR, TABLE_STYLE_HIGHLIGHT_ROW, TABLE_STYLE_HIGHLIGHT_COLUMN)

class PDFReportBuilder:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.page_width, _ = LETTER

    def _format_pct(self, match_count, test_count):
        # Formats percentage with one decimal point (ex. 99.9%)
        if test_count == 0:
            return f"{match_count} (0%)"
        pct = (match_count / test_count) * 100
        return f"{match_count} ({pct:.1f}%)"

    def _label(self, text, style=LABEL_STYLE):
        return Paragraph(text, style)

    def _value(self, text, style=VALUE_STYLE):
        return Paragraph(str(text), style)

    def _logo(self, logo_path, width=300):
        logo = Image(logo_path)
        aspect = logo.imageHeight / logo.imageWidth
        logo.drawWidth = width
        logo.drawHeight = width * aspect

        return logo

    def _table(self, data, col_widths=None, style=None,
        h_align="LEFT", v_align="TOP"):
        table = Table(data, colWidths=col_widths, hAlign=h_align, vAlign=v_align)

        if style:
            table.setStyle(style)

        return table

    def _status_paragraph(self, passed, style=VALUE_STYLE):
        color = PASS_COLOR if passed else FAIL_COLOR
        text = "Pass" if passed else "Fail"
        return self._value(f"<font color='{color}'>{text}</font>", style=style)

    def build(self, audit, filename):
        """Generate a PDF audit report."""

        # Sort test results based on risk-rating.
        tests = sorted(audit.test_results, key=lambda t: (t.is_passing, -t.risk_rating))

        doc = SimpleDocTemplate(
            filename,
            pagesize=LETTER,
            title=f"{audit.title} Audit Report",
            author="AuditOps",
            subject=f"Audit report for {audit.title}",
        )

        elements = []

        # Add logo
        logo_path = str(Path(__file__).resolve().parent / "assets" / "logo.png")
        elements.append(self._logo(logo_path))
        elements.append(Spacer(1, 24))

        # Add title
        elements.append(self._value(f"{audit.title} Audit Report", style=self.styles["Title"]))
        elements.append(Spacer(1, 18))

        # Add cover page table
        elements.append(self._render_cover_page_table(audit))
        elements.append(Spacer(1, 12))

        # Add test results summary (includes all tests in the audit)
        elements.append(Paragraph("Test Summary", self.styles["Heading1"]))
        elements.append(Spacer(1, 12))
        elements.append(self._render_test_summary_table(tests))
        elements.append(PageBreak())

        for test in tests:
            # Build test summary
            elements.append(Spacer(1, 18))
            elements.append(KeepTogether(self._render_test_details_table(test)))
            elements.append(Spacer(1, 12))
            if test.table_headers:
                # Build sample table
                elements.append(KeepTogether(self._render_test_sample_table(test)))
                elements.append(PageBreak())

        doc.build(elements)

    def _render_cover_page_table(self, audit):
        test_count = len(audit.test_results)
        failed = sum(not t.is_passing for t in audit.test_results)
        passed = test_count - failed
        rows = [
            ("Prepared By", "AuditOps"),
            ("Report Date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            ("Tests", test_count),
            ("Passed", self._format_pct(passed, test_count)),
            ("Failed", self._format_pct(failed, test_count))
        ]
        metadata = [
            [self._label(k), self._value(v)]
            for k, v in rows
        ]
        return self._table(metadata, col_widths=[200, 150], style=TABLE_STYLE_HIGHLIGHT_COLUMN, h_align="CENTER")

    def _render_test_summary_table(self, tests):
        # Creates a table summarizing the results of all tests performed in the audit.

        rows = [[
            self._label("Test"),
            self._label("Result"),
            self._label("Risk"),
            self._label("Comments"),
        ]]

        for test in tests:
            rows.append([
                self._value(test.test_description),
                self._status_paragraph(test.is_passing),
                self._value(test.get_risk_rating_str()),
                self._value(test.comments)
            ])
        
        return self._table(rows, col_widths=[220, 60, 70, 140], style=TABLE_STYLE_HIGHLIGHT_ROW)

    def _render_test_details_table(self, test):
        test_procedures = [
            self._value(f"{i+1}. {item}", LIST_STYLE)
            for i, item in enumerate(test.test_procedures)
        ]
        
        # Build summary table
        table_data = [
            [self._label("Test ID"), self._value(test.test_id)],
            [self._label("Test Description"), self._value(test.test_description)],
            [self._label("Risk Rating"), self._value(test.get_risk_rating_str())],
            [self._label("Test Procedures"), test_procedures],
            [self._label("Conclusion"), self._status_paragraph(test.is_passing)],
        ]

        if test.test_attributes:
            test_attributes = [
                self._value(f"• {item}", LIST_STYLE)
                for item in test.test_attributes
            ]
            # Add test attributes only when populated.
            table_data.insert(4, [self._label("Test Attributes"), test_attributes])

        # Add row to summary table if test failed and comments is populated.
        if not test.is_passing and test.comments:
            table_data.append([self._label("Comments"), self._value(test.comments)])

        table_width = self.page_width - 2 * 72
        return self._table(table_data, col_widths=[table_width * 0.25, table_width * 0.75],
         style=TABLE_STYLE_HIGHLIGHT_COLUMN)

    def _render_test_sample_table(self, test):
        # Sort failing samples to top of the table.
        samples = sorted(test.samples, key=lambda s: (s.is_passing))

        table_data = []
        # Build header row (Ex. ["Bucket Name", "Results", "Comments]")
        table_data.append([self._label(h) for h in test.table_headers])
        for i, sample in enumerate(samples, 1):
            row = []
            for val in sample.sample_id.values():
                row.append(self._value(val))

            # Document Result
            if sample.is_excluded:
                row.append(self._value("Excluded", style=CENTER_STYLE))
                row.append(self._value(str(sample.comments)))
            else:
                row.append(self._status_paragraph(sample.is_passing, CENTER_STYLE))
                if not sample.is_passing:
                    # Add comments if sample failed.
                    row.append(self._value(str(sample.comments)))

            table_data.append(row)

        table_width = self.page_width - 2 * 72
        col_width = table_width / len(table_data[0]) # divide evenly across columns
        col_widths = [col_width] * len(table_data[0])
        return self._table(table_data, col_widths=col_widths, style=TABLE_STYLE_HIGHLIGHT_ROW)