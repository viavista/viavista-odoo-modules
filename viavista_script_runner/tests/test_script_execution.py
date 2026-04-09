import base64

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestScriptExecution(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attachment = cls.env['ir.attachment'].create({
            'name': 'products.csv',
            'datas': base64.b64encode(b'id,name\n1,Widget\n2,Gadget'),
        })

    def _create_and_run(self, code, text_params='', file_params=None, description=False, dry_run=False):
        """Helper: create a script, run it, return execution."""
        vals = {
            'name': 'Test',
            'code': code,
            'text_params': text_params,
            'dry_run': dry_run,
        }
        script = self.env['script.script'].create(vals)
        if file_params:
            for name, attachment in file_params.items():
                self.env['script.file.param'].create({
                    'script_id': script.id,
                    'name': name,
                    'attachment_id': attachment.id,
                })
        return script._launch_execution(description=description)

    def test_success_simple(self):
        execution = self._create_and_run('print("hello world")')
        self.assertEqual(execution.state, 'success')
        self.assertEqual(execution.log_output.strip(), 'hello world')
        self.assertTrue(execution.date_end)
        self.assertGreaterEqual(execution.duration, 0)

    def test_success_multiline_print(self):
        code = 'print("line1")\nprint("line2")\nprint("line3")'
        execution = self._create_and_run(code)
        self.assertEqual(execution.state, 'success')
        lines = execution.log_output.strip().split('\n')
        self.assertEqual(lines, ['line1', 'line2', 'line3'])

    def test_success_with_text_params(self):
        code = 'print(f"param={params}")'
        execution = self._create_and_run(code, text_params='hello')
        self.assertEqual(execution.state, 'success')
        self.assertIn('param=hello', execution.log_output)
        self.assertEqual(execution.text_params, 'hello')

    def test_success_with_file_params(self):
        code = (
            'data = files["products"].decode("utf-8")\n'
            'print(f"lines={len(data.splitlines())}")'
        )
        execution = self._create_and_run(
            code,
            file_params={'products': self.attachment},
        )
        self.assertEqual(execution.state, 'success')
        self.assertIn('lines=3', execution.log_output)
        self.assertIn('products: products.csv', execution.file_params_display)

    def test_success_with_env(self):
        code = 'count = env["res.partner"].search_count([])\nprint(f"partners={count}")'
        execution = self._create_and_run(code)
        self.assertEqual(execution.state, 'success')
        self.assertIn('partners=', execution.log_output)

    def test_success_with_imports(self):
        code = (
            'import json as j\n'  # also test that regular imports work
            'd = json.dumps({"a": 1})\n'
            'print(d)\n'
            'print(datetime.date.today())\n'
            'print(re.sub(r"x", "y", "xox"))'
        )
        execution = self._create_and_run(code)
        self.assertEqual(execution.state, 'success')
        self.assertIn('{"a": 1}', execution.log_output)
        self.assertIn('yoy', execution.log_output)

    def test_error_syntax(self):
        execution = self._create_and_run('def bad syntax(')
        self.assertEqual(execution.state, 'error')
        self.assertIn('SyntaxError', execution.error_output)

    def test_error_runtime(self):
        execution = self._create_and_run('raise ValueError("boom")')
        self.assertEqual(execution.state, 'error')
        self.assertIn('ValueError', execution.error_output)
        self.assertIn('boom', execution.error_output)

    def test_error_partial_output(self):
        code = 'print("before")\nraise RuntimeError("after")'
        execution = self._create_and_run(code)
        self.assertEqual(execution.state, 'error')
        self.assertIn('before', execution.log_output)
        self.assertIn('RuntimeError', execution.error_output)

    def test_execution_description(self):
        execution = self._create_and_run(
            'print("ok")',
            description='Monthly import',
        )
        self.assertEqual(execution.description, 'Monthly import')

    def test_execution_user(self):
        execution = self._create_and_run('print(1)')
        self.assertEqual(execution.user_id, self.env.user)

    def test_execution_duration(self):
        execution = self._create_and_run('print(1)')
        self.assertEqual(execution.state, 'success')
        self.assertGreaterEqual(execution.duration, 0)
        self.assertTrue(execution.date_start)
        self.assertTrue(execution.date_end)

    def test_wizard_flow(self):
        script = self.env['script.script'].create({
            'name': 'Wizard Test',
            'code': 'print("via wizard")',
        })
        wizard = self.env['script.run.wizard'].create({
            'script_id': script.id,
            'description': 'test run',
        })
        action = wizard.action_confirm()
        self.assertEqual(action['res_model'], 'script.execution')

        execution = self.env['script.execution'].browse(action['res_id'])
        self.assertEqual(execution.state, 'success')
        self.assertEqual(execution.description, 'test run')
        self.assertIn('via wizard', execution.log_output)

    def test_dry_run_rollback(self):
        """Dry run captures output but rolls back DB changes."""
        partner_name = 'DryRunTestPartner_XYZ'
        code = (
            f'p = env["res.partner"].create({{"name": "{partner_name}"}})\n'
            f'print(f"created {{p.name}}")'
        )
        execution = self._create_and_run(code, dry_run=True)
        self.assertEqual(execution.state, 'success')
        self.assertTrue(execution.dry_run)
        self.assertIn(f'created {partner_name}', execution.log_output)
        # Partner should NOT exist — savepoint was rolled back
        partner = self.env['res.partner'].search([('name', '=', partner_name)])
        self.assertFalse(partner, "Dry run should rollback DB changes")
        # Summary should list the created record
        self.assertIn('DRY RUN SUMMARY', execution.log_output)
        self.assertIn('res.partner', execution.log_output)
        self.assertIn('Created:', execution.log_output)
        self.assertIn('All changes have been rolled back.', execution.log_output)

    def test_dry_run_error(self):
        """Dry run with error still captures partial output and rolls back."""
        code = 'print("before error")\nraise ValueError("dry boom")'
        execution = self._create_and_run(code, dry_run=True)
        self.assertEqual(execution.state, 'error')
        self.assertTrue(execution.dry_run)
        self.assertIn('before error', execution.log_output)
        self.assertIn('dry boom', execution.error_output)

    def test_dry_run_wizard(self):
        """Wizard reads dry_run from script model."""
        script = self.env['script.script'].create({
            'name': 'Dry Wizard Test',
            'code': 'print("dry wizard")',
            'dry_run': True,
        })
        wizard = self.env['script.run.wizard'].create({
            'script_id': script.id,
        })
        action = wizard.action_confirm()
        execution = self.env['script.execution'].browse(action['res_id'])
        self.assertEqual(execution.state, 'success')
        self.assertTrue(execution.dry_run)
        self.assertIn('dry wizard', execution.log_output)

    def test_output_truncation(self):
        """Output exceeding 1 MB is truncated to prevent OOM."""
        code = 'for i in range(200000): print("x" * 100)'
        execution = self._create_and_run(code)
        self.assertEqual(execution.state, 'success')
        self.assertIn('Output truncated', execution.log_output)
        self.assertLess(len(execution.log_output), 1_100_000)

    def test_mark_failed(self):
        """Stuck running executions can be manually marked as failed."""
        script = self.env['script.script'].create({
            'name': 'Stuck Test',
            'code': 'print("ok")',
        })
        execution = self.env['script.execution'].create({
            'script_id': script.id,
            'script_name': script.name,
            'state': 'running',
        })
        execution.action_mark_failed()
        self.assertEqual(execution.state, 'error')
        self.assertIn('Manually marked as failed', execution.error_output)

    def test_mark_failed_noop_on_success(self):
        """Marking a successful execution does nothing."""
        execution = self._create_and_run('print("ok")')
        self.assertEqual(execution.state, 'success')
        execution.action_mark_failed()
        self.assertEqual(execution.state, 'success')

    def test_empty_code(self):
        """Empty code string executes successfully (no-op)."""
        execution = self._create_and_run('')
        self.assertEqual(execution.state, 'success')

    def test_dry_run_with_write_and_delete(self):
        """Dry run summary shows Modified and Deleted sections."""
        partner = self.env['res.partner'].create({'name': 'DryRunModTarget'})
        pid = partner.id
        code = (
            f'p = env["res.partner"].browse({pid})\n'
            f'p.write({{"phone": "+123"}})\n'
            f'p.unlink()\n'
            f'print("done")'
        )
        execution = self._create_and_run(code, dry_run=True)
        self.assertEqual(execution.state, 'success')
        self.assertIn('Modified:', execution.log_output)
        self.assertIn('Deleted:', execution.log_output)
        # Record should still exist — savepoint rolled back
        self.assertTrue(self.env['res.partner'].browse(pid).exists())

    def test_duplicate_file_param_name_rejected(self):
        """Two file params with the same name on the same script raises error."""
        script = self.env['script.script'].create({
            'name': 'Dup Test',
            'code': 'pass',
        })
        attachment = self.attachment
        self.env['script.file.param'].create({
            'script_id': script.id,
            'name': 'data',
            'attachment_id': attachment.id,
        })
        with self.assertRaises(ValidationError):
            self.env['script.file.param'].create({
                'script_id': script.id,
                'name': 'data',
                'attachment_id': attachment.id,
            })
