"""Google API authentication."""
from pathlib import Path
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

class GSCAuthenticator:
    def __init__(self, service_account_path: Optional[Path] = None):
        self.service_account_path = service_account_path
    
    def get_service(self):
        if self.service_account_path and self.service_account_path.exists():
            credentials = service_account.Credentials.from_service_account_file(
                str(self.service_account_path), scopes=SCOPES
            )
            return build("searchconsole", "v1", credentials=credentials)
        raise ValueError("Service account credentials required")
