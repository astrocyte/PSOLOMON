"""WordPress CLI wrapper for remote execution via SSH."""

import json
import paramiko
from typing import Any, Optional
from .config import WordPressConfig


class WPCLIError(Exception):
    """Exception raised for wp-cli command errors."""
    pass


class WPCLIClient:
    """Client for executing wp-cli commands remotely."""

    def __init__(self, config: WordPressConfig):
        self.config = config
        self.ssh_client: Optional[paramiko.SSHClient] = None

    def connect(self):
        """Establish SSH connection."""
        if self.ssh_client is not None:
            return

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs = {
            "hostname": self.config.ssh_host,
            "username": self.config.ssh_user,
            "port": self.config.ssh_port,
        }

        if self.config.ssh_key_path:
            connect_kwargs["key_filename"] = self.config.ssh_key_path
        elif self.config.ssh_password:
            connect_kwargs["password"] = self.config.ssh_password
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False

        self.ssh_client.connect(**connect_kwargs)

    def disconnect(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def execute(self, command: str, format: str = "json") -> Any:
        """
        Execute a wp-cli command.

        Args:
            command: wp-cli command (without 'wp' prefix)
            format: Output format (json, csv, table, etc.)

        Returns:
            Command output (parsed JSON if format=json)
        """
        self.connect()

        # Build full command
        if format and format != "table":
            full_command = f"cd {self.config.remote_path} && wp {command} --format={format}"
        else:
            full_command = f"cd {self.config.remote_path} && wp {command}"

        # Execute command
        stdin, stdout, stderr = self.ssh_client.exec_command(full_command)
        exit_code = stdout.channel.recv_exit_status()

        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()

        if exit_code != 0:
            raise WPCLIError(f"wp-cli command failed: {error or output}")

        # Parse JSON output if requested
        if format == "json" and output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return output

        return output

    def get_info(self) -> dict:
        """Get WordPress site information."""
        core_version = self.execute("core version", format=None)
        site_url = self.execute("option get siteurl", format=None)
        site_title = self.execute("option get blogname", format=None)

        return {
            "version": core_version,
            "url": site_url,
            "title": site_title,
        }

    def list_plugins(self, status: Optional[str] = None) -> list[dict]:
        """
        List installed plugins.

        Args:
            status: Filter by status (active, inactive, must-use)
        """
        cmd = "plugin list"
        if status:
            cmd += f" --status={status}"

        return self.execute(cmd, format="json")

    def list_themes(self) -> list[dict]:
        """List installed themes."""
        return self.execute("theme list", format="json")

    def search_posts(self, search: str, post_type: str = "post") -> list[dict]:
        """
        Search for posts.

        Args:
            search: Search query
            post_type: Post type to search (post, page, etc.)
        """
        cmd = f"post list --post_type={post_type} --s='{search}'"
        return self.execute(cmd, format="json")

    def list_posts(
        self,
        post_type: str = "post",
        post_status: str = "publish",
        limit: int = 10
    ) -> list[dict]:
        """
        List posts.

        Args:
            post_type: Post type (post, page, etc.)
            post_status: Post status (publish, draft, etc.)
            limit: Number of posts to return
        """
        cmd = f"post list --post_type={post_type} --post_status={post_status} --posts_per_page={limit}"
        return self.execute(cmd, format="json")

    def get_post(self, post_id: int) -> dict:
        """Get post details by ID."""
        return self.execute(f"post get {post_id}", format="json")

    def check_updates(self) -> dict:
        """Check for available updates."""
        return {
            "core": self.execute("core check-update", format="json"),
            "plugins": self.execute("plugin list --update=available", format="json"),
            "themes": self.execute("theme list --update=available", format="json"),
        }
