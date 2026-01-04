"""Export format handlers."""
from typing import TYPE_CHECKING

# Lazy import to avoid requiring weasyprint by default
if TYPE_CHECKING:
    from .pdf import PDFExporter, export_to_pdf


def get_pdf_exporter():
    """Get PDF exporter (requires weasyprint)."""
    from .pdf import PDFExporter

    return PDFExporter()


__all__ = ["get_pdf_exporter"]
