"""WordPress Backup Manager for MCP Server."""

import os
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Optional
import paramiko
from .config import WordPressConfig


class BackupError(Exception):
    """Exception raised for backup errors."""
    pass


class BackupManager:
    """Manages WordPress site backups via SSH."""

    def __init__(self, config: WordPressConfig, local_backup_dir: str = "./backups"):
        self.config = config
        self.local_backup_dir = Path(local_backup_dir)
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

    def create_backup(self, include_files: bool = True, include_database: bool = True) -> dict:
        """
        Create a complete WordPress backup.

        Args:
            include_files: Include wp-content directory
            include_database: Include database dump

        Returns:
            dict with backup information
        """
        self.connect()

        # Create backup directory
        self.local_backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"sst_nyc_{timestamp}"
        backup_path = self.local_backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)

        results = {
            "timestamp": timestamp,
            "backup_name": backup_name,
            "backup_path": str(backup_path),
            "files_backed_up": False,
            "database_backed_up": False,
            "archive_created": False,
            "total_size": "0 MB",
        }

        try:
            # 1. Backup Database
            if include_database:
                db_file = backup_path / "database.sql"
                self._backup_database(db_file)
                results["database_backed_up"] = True
                results["database_size"] = self._get_file_size(db_file)

            # 2. Backup wp-content
            if include_files:
                wp_content_dir = backup_path / "wp-content"
                self._backup_files(wp_content_dir)
                results["files_backed_up"] = True
                results["files_size"] = self._get_dir_size(wp_content_dir)

            # 3. Backup wp-config.php
            if include_files:
                wp_config_file = backup_path / "wp-config.php"
                self._backup_wp_config(wp_config_file)

            # 4. Create compressed archive
            archive_path = self.local_backup_dir / f"{backup_name}.tar.gz"
            self._create_archive(backup_path, archive_path)
            results["archive_created"] = True
            results["archive_path"] = str(archive_path)
            results["total_size"] = self._get_file_size(archive_path)

            # Clean up uncompressed files
            self._cleanup_directory(backup_path)

            return results

        except Exception as e:
            raise BackupError(f"Backup failed: {str(e)}")
        finally:
            self.disconnect()

    def _backup_database(self, local_path: Path):
        """Backup WordPress database."""
        command = f"cd {self.config.remote_path} && wp db export - --allow-root"
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()

        if exit_code != 0:
            error = stderr.read().decode('utf-8')
            raise BackupError(f"Database backup failed: {error}")

        # Write database dump to file
        with open(local_path, 'wb') as f:
            f.write(stdout.read())

    def _backup_files(self, local_path: Path):
        """Backup wp-content directory."""
        local_path.mkdir(parents=True, exist_ok=True)

        # Use SFTP to download wp-content recursively
        sftp = self.ssh_client.open_sftp()
        remote_wp_content = f"{self.config.remote_path}/wp-content"

        try:
            self._sftp_download_recursive(sftp, remote_wp_content, str(local_path))
        finally:
            sftp.close()

    def _backup_wp_config(self, local_path: Path):
        """Backup wp-config.php."""
        sftp = self.ssh_client.open_sftp()
        remote_config = f"{self.config.remote_path}/wp-config.php"

        try:
            sftp.get(remote_config, str(local_path))
        except Exception:
            # wp-config.php might not be readable, skip
            pass
        finally:
            sftp.close()

    def _sftp_download_recursive(self, sftp: paramiko.SFTPClient, remote_dir: str, local_dir: str):
        """Recursively download directory via SFTP."""
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)

        for item in sftp.listdir_attr(remote_dir):
            remote_path = f"{remote_dir}/{item.filename}"
            local_item = local_path / item.filename

            if item.st_mode & 0o40000:  # Directory
                self._sftp_download_recursive(sftp, remote_path, str(local_item))
            else:  # File
                sftp.get(remote_path, str(local_item))

    def _create_archive(self, source_dir: Path, archive_path: Path):
        """Create compressed tar.gz archive."""
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)

    def _cleanup_directory(self, directory: Path):
        """Remove directory and all contents."""
        import shutil
        if directory.exists():
            shutil.rmtree(directory)

    def _get_file_size(self, file_path: Path) -> str:
        """Get human-readable file size."""
        size_bytes = file_path.stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _get_dir_size(self, directory: Path) -> str:
        """Get human-readable directory size."""
        total_size = sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
        size_bytes = total_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def list_backups(self) -> list[dict]:
        """List all available local backups."""
        backups = []

        if not self.local_backup_dir.exists():
            return backups

        for backup_file in self.local_backup_dir.glob("*.tar.gz"):
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": self._get_file_size(backup_file),
                "created": datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def delete_backup(self, backup_filename: str) -> bool:
        """Delete a backup file."""
        backup_path = self.local_backup_dir / backup_filename
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
