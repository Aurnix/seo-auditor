"""Secrets management."""
import os
from typing import Protocol

class SecretsBackend(Protocol):
    def get_secret(self, key: str) -> str: ...

class EnvVarSecrets:
    def get_secret(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Missing: {key}")
        return value

def get_secrets_backend() -> SecretsBackend:
    return EnvVarSecrets()
