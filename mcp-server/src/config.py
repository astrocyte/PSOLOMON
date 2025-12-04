"""Configuration management for WordPress MCP Server."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class WordPressConfig:
    """WordPress site configuration."""

    site_url: str
    ssh_host: str
    ssh_user: str
    ssh_key_path: Optional[str]
    remote_path: str
    api_user: str
    api_password: str
    ssh_port: int = 22
    ssh_password: Optional[str] = None
    jwt_token: Optional[str] = None
    db_host: Optional[str] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    mailchimp_api_key: Optional[str] = None
    mailchimp_server: Optional[str] = None
    mailchimp_list_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "WordPressConfig":
        """Load configuration from environment variables."""
        return cls(
            site_url=os.getenv("WP_SITE_URL", ""),
            ssh_host=os.getenv("WP_SSH_HOST", ""),
            ssh_user=os.getenv("WP_SSH_USER", ""),
            ssh_key_path=os.getenv("WP_SSH_KEY_PATH"),
            remote_path=os.getenv("WP_REMOTE_PATH", "/var/www/html"),
            api_user=os.getenv("WP_API_USER", ""),
            api_password=os.getenv("WP_API_PASSWORD", ""),
            ssh_port=int(os.getenv("WP_SSH_PORT", "22")),
            ssh_password=os.getenv("WP_SSH_PASSWORD"),
            jwt_token=os.getenv("WP_JWT_TOKEN"),
            db_host=os.getenv("WP_DB_HOST"),
            db_name=os.getenv("WP_DB_NAME"),
            db_user=os.getenv("WP_DB_USER"),
            db_password=os.getenv("WP_DB_PASSWORD"),
            mailchimp_api_key=os.getenv("MAILCHIMP_API_KEY"),
            mailchimp_server=os.getenv("MAILCHIMP_SERVER"),
            mailchimp_list_id=os.getenv("MAILCHIMP_LIST_ID"),
        )

    def validate(self) -> list[str]:
        """Validate required configuration."""
        errors = []

        if not self.site_url:
            errors.append("WP_SITE_URL is required")
        if not self.ssh_host:
            errors.append("WP_SSH_HOST is required")
        if not self.ssh_user:
            errors.append("WP_SSH_USER is required")
        if not self.api_user:
            errors.append("WP_API_USER is required")
        if not self.api_password:
            errors.append("WP_API_PASSWORD is required")

        if self.ssh_key_path and not Path(self.ssh_key_path).exists():
            errors.append(f"SSH key not found: {self.ssh_key_path}")

        return errors
