import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestScriptCrud(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.script = cls.env['script.script'].create({
            'name': 'Test Script',
            'code': 'print("hello")',
            'text_params': 'test-param',
        })

    def test_script_create(self):
        self.assertEqual(self.script.name, 'Test Script')
        self.assertEqual(self.script.text_params, 'test-param')
        self.assertTrue(self.script.active)

    def test_script_defaults(self):
        script = self.env['script.script'].create({
            'name': 'Defaults',
            'code': '# noop',
        })
        self.assertTrue(script.active)
        self.assertEqual(script.text_params, '')
        self.assertEqual(script.execution_count, 0)

    def test_file_param_create(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'test.txt',
            'datas': base64.b64encode(b'file content'),
        })
        file_param = self.env['script.file.param'].create({
            'script_id': self.script.id,
            'name': 'my-file',
            'attachment_id': attachment.id,
        })
        self.assertEqual(file_param.name, 'my-file')
        self.assertEqual(file_param.attachment_id, attachment)
        self.assertIn(file_param, self.script.file_param_ids)

    def test_file_param_cascade_delete(self):
        attachment = self.env['ir.attachment'].create({
            'name': 'test.txt',
            'datas': base64.b64encode(b'data'),
        })
        self.env['script.file.param'].create({
            'script_id': self.script.id,
            'name': 'fp',
            'attachment_id': attachment.id,
        })
        fp_count = self.env['script.file.param'].search_count([
            ('script_id', '=', self.script.id),
        ])
        self.assertEqual(fp_count, 1)

        self.script.unlink()
        fp_count = self.env['script.file.param'].search_count([
            ('script_id', '=', self.script.id),
        ])
        self.assertEqual(fp_count, 0)

    def test_execution_survives_script_delete(self):
        """Deleting a script sets execution.script_id to null but keeps the record."""
        script = self.env['script.script'].create({
            'name': 'Will Be Deleted',
            'code': 'print("ok")',
        })
        execution = script._launch_execution()
        exec_id = execution.id
        script_name = script.name

        script.unlink()

        execution = self.env['script.execution'].browse(exec_id)
        self.assertTrue(execution.exists())
        self.assertFalse(execution.script_id)
        self.assertEqual(execution.script_name, script_name)

    def test_execution_count(self):
        self.assertEqual(self.script.execution_count, 0)
        self.env['script.execution'].create({
            'script_id': self.script.id,
            'script_name': self.script.name,
            'state': 'success',
        })
        self.script.invalidate_recordset()
        self.assertEqual(self.script.execution_count, 1)

    def test_action_run_returns_wizard(self):
        action = self.script.action_run()
        self.assertEqual(action['res_model'], 'script.run.wizard')
        self.assertEqual(action['target'], 'new')

    def test_action_view_executions(self):
        action = self.script.action_view_executions()
        self.assertEqual(action['res_model'], 'script.execution')
        self.assertIn(('script_id', '=', self.script.id), action['domain'])
