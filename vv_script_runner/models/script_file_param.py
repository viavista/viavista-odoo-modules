from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ScriptFileParam(models.Model):
    _name = 'script.file.param'
    _description = 'Script File Parameter'

    script_id = fields.Many2one('script.script', required=True, ondelete='cascade')
    name = fields.Char(required=True, help='Parameter name, e.g. "products-file"')
    attachment_id = fields.Many2one('ir.attachment', required=True, string='File')

    @api.constrains('name', 'script_id')
    def _check_unique_name(self):
        for rec in self:
            duplicates = self.search_count([
                ('script_id', '=', rec.script_id.id),
                ('name', '=', rec.name),
                ('id', '!=', rec.id),
            ])
            if duplicates:
                raise ValidationError(
                    _("Duplicate file parameter name '%(name)s'.", name=rec.name)
                )
