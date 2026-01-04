"""Dashboard renderer."""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from ..models.report import AuditReport

class DashboardRenderer:
    def __init__(self):
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    def render(self, report: AuditReport, output_path: Path) -> None:
        template = self.env.get_template("dashboard.html")
        html = template.render(report=report)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
