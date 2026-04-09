from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    viavista_monitoring_delete_after_days = fields.Integer(
        string="Delete After (days)",
        default=30,
        help="Permanently delete log entries older than this many days.",
        config_parameter="viavista_monitoring.delete_after_days",
    )
    viavista_monitoring_agent_enabled = fields.Boolean(
        string="Backup Agent Installed",
        default=False,
        help="Enable if the Viavista health agent container is running "
        "alongside this Odoo instance.",
        config_parameter="viavista_monitoring.agent_enabled",
    )
    viavista_monitoring_agent_status_path = fields.Char(
        string="Agent Status File Path",
        default="/var/lib/odoo/health/agent_status.json",
        help="Path to the agent's status JSON file.",
        config_parameter="viavista_monitoring.agent_status_path",
    )
