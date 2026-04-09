from odoo import models, fields


class ScriptRunWizard(models.TransientModel):
    _name = 'script.run.wizard'
    _description = 'Run Script Wizard'

    script_id = fields.Many2one('script.script', required=True, readonly=True)
    description = fields.Text(string='Reason / Description')

    def action_confirm(self):
        self.ensure_one()
        execution = self.script_id._launch_execution(description=self.description)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'script.execution',
            'res_id': execution.id,
            'view_mode': 'form',
            'target': 'current',
        }
