"""PDF exporter using WeasyPrint."""
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from ...models.report import AuditReport


class PDFExporter:
    """Export audit reports to PDF format.

    Requires weasyprint to be installed:
        pip install weasyprint

    Or install with pdf extras:
        pip install seo-auditor[pdf]
    """

    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "weasyprint is required for PDF export. "
                "Install with: pip install seo-auditor[pdf]"
            )
        template_dir = Path(__file__).parent.parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
        self.font_config = FontConfiguration()

    def export(
        self,
        report: AuditReport,
        output_path: Path,
        include_charts: bool = False,
    ) -> None:
        """Export audit report to PDF.

        Args:
            report: The audit report to export
            output_path: Path for the output PDF file
            include_charts: Whether to include chart placeholders (charts won't render in PDF)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Render HTML with PDF-specific template
        template = self.env.get_template("pdf_report.html")
        html_content = template.render(report=report, include_charts=include_charts)

        # Convert to PDF
        html = HTML(string=html_content)
        html.write_pdf(
            str(output_path),
            stylesheets=[CSS(string=self._get_pdf_styles())],
            font_config=self.font_config,
        )

    def _get_pdf_styles(self) -> str:
        """Get CSS styles optimized for PDF output."""
        return """
        @page {
            size: A4;
            margin: 2cm;
            @top-right {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #1f2937;
        }

        h1 { font-size: 20pt; margin-bottom: 0.5em; color: #111827; }
        h2 { font-size: 14pt; margin-top: 1.5em; margin-bottom: 0.5em; color: #374151; }
        h3 { font-size: 12pt; margin-top: 1em; margin-bottom: 0.5em; color: #4b5563; }

        .header {
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 1em;
            margin-bottom: 2em;
        }

        .score-box {
            display: inline-block;
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #f3f4f6;
            text-align: center;
            line-height: 80px;
            font-size: 24pt;
            font-weight: bold;
            margin-right: 1em;
        }

        .score-box.good { background: #dcfce7; color: #16a34a; }
        .score-box.medium { background: #fef3c7; color: #d97706; }
        .score-box.poor { background: #fee2e2; color: #dc2626; }

        .stats-grid {
            display: table;
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
        }

        .stats-grid .stat {
            display: table-cell;
            width: 25%;
            padding: 0.75em;
            text-align: center;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
        }

        .stats-grid .stat-value {
            font-size: 18pt;
            font-weight: bold;
            color: #111827;
        }

        .stats-grid .stat-label {
            font-size: 9pt;
            color: #6b7280;
        }

        .issue-card {
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            padding: 0.75em;
            margin-bottom: 0.75em;
            page-break-inside: avoid;
        }

        .issue-card.priority-critical {
            border-left: 4px solid #dc2626;
            background: #fef2f2;
        }
        .issue-card.priority-high {
            border-left: 4px solid #f97316;
            background: #fff7ed;
        }
        .issue-card.priority-medium {
            border-left: 4px solid #eab308;
            background: #fefce8;
        }
        .issue-card.priority-low {
            border-left: 4px solid #22c55e;
            background: #f0fdf4;
        }

        .priority-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 8pt;
            font-weight: bold;
            text-transform: uppercase;
        }

        .priority-badge.critical { background: #dc2626; color: white; }
        .priority-badge.high { background: #f97316; color: white; }
        .priority-badge.medium { background: #eab308; color: #1f2937; }
        .priority-badge.low { background: #22c55e; color: white; }

        .action-item {
            display: table;
            width: 100%;
            margin-bottom: 0.5em;
            page-break-inside: avoid;
        }

        .action-rank {
            display: table-cell;
            width: 30px;
            height: 30px;
            background: #3b82f6;
            color: white;
            text-align: center;
            line-height: 30px;
            border-radius: 50%;
            font-weight: bold;
            vertical-align: top;
        }

        .action-content {
            display: table-cell;
            padding-left: 1em;
            vertical-align: top;
        }

        .findings-list {
            list-style: none;
            padding: 0;
        }

        .findings-list li {
            padding: 0.25em 0 0.25em 1.5em;
            position: relative;
        }

        .findings-list li:before {
            content: "•";
            position: absolute;
            left: 0.5em;
            color: #ef4444;
        }

        .quick-wins-list li:before {
            color: #22c55e;
        }

        table.data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
            margin: 1em 0;
        }

        table.data-table th,
        table.data-table td {
            border: 1px solid #e5e7eb;
            padding: 0.5em;
            text-align: left;
        }

        table.data-table th {
            background: #f3f4f6;
            font-weight: 600;
        }

        .footer {
            margin-top: 2em;
            padding-top: 1em;
            border-top: 1px solid #e5e7eb;
            font-size: 9pt;
            color: #6b7280;
            text-align: center;
        }

        .page-break {
            page-break-before: always;
        }
        """


def export_to_pdf(report: AuditReport, output_path: Path) -> None:
    """Convenience function to export a report to PDF.

    Args:
        report: The audit report to export
        output_path: Path for the output PDF file
    """
    exporter = PDFExporter()
    exporter.export(report, output_path)
