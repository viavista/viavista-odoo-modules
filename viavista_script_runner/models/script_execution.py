from odoo import models, fields, _


class ScriptExecution(models.Model):
    _name = 'script.execution'
    _description = 'Script Execution'
    _order = 'date_start desc'

    script_id = fields.Many2one('script.script', ondelete='set null')
    script_name = fields.Char(string='Script Name')
    user_id = fields.Many2one('res.users', string='Run By', default=lambda self: self.env.user)
    description = fields.Text(string='Run Description')
    dry_run = fields.Boolean(string='Dry Run', default=False)
    state = fields.Selection([
        ('running', 'Running'),
        ('success', 'Success'),
        ('error', 'Error'),
    ], default='running', required=True)
    date_start = fields.Datetime(default=fields.Datetime.now)
    date_end = fields.Datetime()
    duration = fields.Float(string='Duration (s)', digits=(16, 3))
    text_params = fields.Text(string='Text Parameters')
    file_params_display = fields.Text(string='File Parameters')
    log_output = fields.Text(string='Log Output')
    error_output = fields.Text(string='Error Output')

    def action_mark_failed(self):
        """Allow admins to mark stuck 'running' executions as failed."""
        for rec in self:
            if rec.state == 'running':
                rec.write({
                    'state': 'error',
                    'date_end': fields.Datetime.now(),
                    'error_output': _(
                        "Manually marked as failed by %(user)s.\n"
                        "The original execution may have been interrupted "
                        "by a server restart or crash.",
                        user=self.env.user.name,
                    ),
                })
