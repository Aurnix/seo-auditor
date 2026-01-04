"""Screaming Frog export definitions."""
from enum import Enum
from dataclasses import dataclass

class ExportType(str, Enum):
    INTERNAL_HTML = "internal:html"
    INTERNAL_ALL = "internal:all"
    RESPONSE_CODES_ALL = "response_codes:all"
    PAGE_TITLES_ALL = "page_titles:all"
    META_DESCRIPTION_ALL = "meta_description:all"
    H1_ALL = "h1:all"
    IMAGES_ALL = "images:all"
    ALL_INLINKS = "all_inlinks"
    CANONICALS_ALL = "canonicals:all"
    DIRECTIVES_ALL = "directives:all"
    REDIRECTS_ALL = "redirects:all"

@dataclass
class ExportConfig:
    export_type: ExportType
    filename: str
    required: bool = True

DEFAULT_EXPORTS = [
    ExportConfig(ExportType.INTERNAL_HTML, "internal_html.csv"),
    ExportConfig(ExportType.PAGE_TITLES_ALL, "page_titles_all.csv"),
    ExportConfig(ExportType.META_DESCRIPTION_ALL, "meta_description_all.csv"),
    ExportConfig(ExportType.H1_ALL, "h1_all.csv"),
    ExportConfig(ExportType.IMAGES_ALL, "images_all.csv", required=False),
    ExportConfig(ExportType.ALL_INLINKS, "all_inlinks.csv"),
    ExportConfig(ExportType.CANONICALS_ALL, "canonicals_all.csv"),
]
