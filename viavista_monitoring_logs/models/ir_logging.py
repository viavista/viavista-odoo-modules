import json
import logging
import os
from datetime import timedelta

from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)

MAX_AGENT_STATUS_SIZE = 1_000_000  # 1 MB
ALLOWED_AGENT_PATH_PREFIX = "/var/lib/odoo/"  # must end with /
DEFAULT_AGENT_STATUS_PATH = "/var/lib/odoo/health/agent_status.json"
CLEANUP_BATCH_SIZE = 1000


class IrLogging(models.Model):
    _inherit = "ir.logging"

    def init(self):
        """Add index on create_date for efficient retention and issue scanning."""
        self.env.cr.execute("""
            CREATE INDEX IF NOT EXISTS ir_logging_create_date_idx
            ON ir_logging (create_date)
        """)

    @api.model
    def _cron_retention(self):
        """Delete old log records based on configured retention."""
        ICP = self.env["ir.config_parameter"].sudo()

        try:
            delete_days = int(
                ICP.get_param("viavista_monitoring.delete_after_days", "30")
            )
        except (ValueError, TypeError):
            delete_days = 30
        if delete_days < 1:
            delete_days = 30

        cutoff = fields.Datetime.now() - timedelta(days=delete_days)
        deleted = self.sudo().search(
            [("create_date", "<", cutoff)], limit=CLEANUP_BATCH_SIZE
        )
        if deleted:
            count = len(deleted)
            deleted.unlink()
            _logger.info(
                "viavista_monitoring_logs: deleted %d records older than %d days",
                count,
                delete_days,
            )

    @api.model
    def _cron_read_agent_status(self):
        """Read agent status JSON and create backup log entries."""
        ICP = self.env["ir.config_parameter"].sudo()

        if not tools.str2bool(
            ICP.get_param("viavista_monitoring.agent_enabled", "False")
        ):
            return

        agent_path = ICP.get_param(
            "viavista_monitoring.agent_status_path", DEFAULT_AGENT_STATUS_PATH
        )

        # Path validation
        real_path = os.path.realpath(agent_path)
        if not real_path.startswith(ALLOWED_AGENT_PATH_PREFIX):
            _logger.warning(
                "Agent status path %s is outside allowed prefix, skipping",
                real_path,
            )
            return

        agent_data = self._read_agent_json(real_path)
        if not agent_data:
            return

        self._check_backup_change(agent_data, ICP)

    @api.model
    def _read_agent_json(self, path):
        """Read agent status JSON file with size limit."""
        try:
            with open(path) as f:
                raw = f.read(MAX_AGENT_STATUS_SIZE)
                return json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return None

    @api.model
    def _check_backup_change(self, agent_data, ICP):
        """Detect new backup and create ir.logging entry."""
        last_backup = agent_data.get("last_backup", "")
        if not last_backup:
            return

        prev_backup = ICP.get_param(
            "viavista_monitoring.last_reported_backup", ""
        )
        if last_backup == prev_backup:
            return

        backup_status = agent_data.get("backup_status", "ok")
        size_mb = agent_data.get("backup_size_mb", 0)

        if backup_status == "ok":
            level = "INFO"
            message = "Backup completed: %.1f MB" % size_mb
        else:
            level = "ERROR"
            error_msg = agent_data.get("backup_error", "Unknown error")
            message = "Backup failed: %s" % error_msg

        # Create ir.logging record via raw SQL (same pattern as Odoo's PostgreSQLHandler)
        self.env.cr.execute(
            """
            INSERT INTO ir_logging
                (create_date, write_date, create_uid, write_uid,
                 name, type, dbname, level, message, path, func, line)
            VALUES
                (NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC', %s, %s,
                 %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                self.env.uid,
                self.env.uid,
                "viavista.agent.backup",
                "server",
                self.env.cr.dbname,
                level,
                message,
                "agent/backup.py",
                "run",
                "0",
            ),
        )

        ICP.set_param("viavista_monitoring.last_reported_backup", last_backup)
        _logger.info("Backup status recorded: %s", message)
