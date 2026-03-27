import ctypes
import functools
import logging
import threading
import time
import traceback
from io import StringIO

from odoo import models, fields, api, modules, _
from odoo.modules.registry import Registry

_logger = logging.getLogger(__name__)

# Maximum captured output size (characters). Protects against OOM from
# scripts that print in a loop. The dry-run summary is exempt from this limit.
MAX_OUTPUT_SIZE = 1_000_000  # 1 MB


def _make_print(stdout_capture):
    """Create a size-limited print function that writes to stdout_capture."""
    truncated = False

    def custom_print(*args, **kwargs):
        nonlocal truncated
        if truncated:
            return
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')
        stdout_capture.write(sep.join(str(a) for a in args) + end)
        if stdout_capture.tell() >= MAX_OUTPUT_SIZE:
            truncated = True
            stdout_capture.write(
                '\n--- Output truncated (exceeded 1 MB limit) ---\n'
            )

    return custom_print


# Thread-local tracker for dry-run change tracking
_dry_run_tracker = threading.local()
_hooks_lock = threading.Lock()

# Internal models to skip in dry-run summary (too noisy)
_SKIP_TRACK_MODELS = frozenset({
    'ir.model.data', 'ir.property', 'ir.attachment',
    'bus.bus', 'bus.presence',
    'mail.message', 'mail.followers', 'mail.notification',
    'mail.activity', 'mail.mail',
})


def _install_dry_run_hooks():
    """Patch BaseModel.create/write/unlink to track changes during dry run.

    Installed before each dry-run and removed after, so hooks are only
    active while a dry-run is executing — zero overhead at other times.
    """
    from odoo.orm.models import BaseModel
    if getattr(BaseModel, '_vv_dry_run_hooks', False):
        return

    with _hooks_lock:
        if getattr(BaseModel, '_vv_dry_run_hooks', False):
            return

        orig_create = BaseModel.create
        orig_write = BaseModel.write
        orig_unlink = BaseModel.unlink

        @functools.wraps(orig_create)
        def tracked_create(self, vals_list):
            result = orig_create(self, vals_list)
            tracker = getattr(_dry_run_tracker, 'data', None)
            if tracker is not None and self._name not in _SKIP_TRACK_MODELS:
                for rec in result:
                    try:
                        name = rec.display_name
                    except Exception:
                        name = str(rec.id)
                    tracker['created'].append((rec._name, rec.id, name))
            return result

        @functools.wraps(orig_write)
        def tracked_write(self, vals):
            tracker = getattr(_dry_run_tracker, 'data', None)
            if tracker is not None and self._name not in _SKIP_TRACK_MODELS:
                for rec in self:
                    try:
                        name = rec.display_name
                    except Exception:
                        name = str(rec.id)
                    tracker['written'][(rec._name, rec.id)] = name
            return orig_write(self, vals)

        @functools.wraps(orig_unlink)
        def tracked_unlink(self):
            tracker = getattr(_dry_run_tracker, 'data', None)
            if tracker is not None and self._name not in _SKIP_TRACK_MODELS:
                for rec in self:
                    try:
                        name = rec.display_name
                    except Exception:
                        name = str(rec.id)
                    tracker['deleted'].append((rec._name, rec.id, name))
            return orig_unlink(self)

        BaseModel.create = tracked_create
        BaseModel.write = tracked_write
        BaseModel.unlink = tracked_unlink
        BaseModel._vv_dry_run_hooks = True
        BaseModel._vv_orig_create = orig_create
        BaseModel._vv_orig_write = orig_write
        BaseModel._vv_orig_unlink = orig_unlink


def _uninstall_dry_run_hooks():
    """Remove dry-run hooks from BaseModel, restoring originals."""
    from odoo.orm.models import BaseModel
    if not getattr(BaseModel, '_vv_dry_run_hooks', False):
        return

    with _hooks_lock:
        if not getattr(BaseModel, '_vv_dry_run_hooks', False):
            return
        BaseModel.create = BaseModel._vv_orig_create
        BaseModel.write = BaseModel._vv_orig_write
        BaseModel.unlink = BaseModel._vv_orig_unlink
        del BaseModel._vv_dry_run_hooks
        del BaseModel._vv_orig_create
        del BaseModel._vv_orig_write
        del BaseModel._vv_orig_unlink


def _raise_timeout_in_thread(thread_ident):
    """Raise TimeoutError asynchronously in the given thread."""
    ctypes.pythonapi.PyThreadState_SetAsyncExc(
        ctypes.c_ulong(thread_ident),
        ctypes.py_object(TimeoutError),
    )


def _format_dry_run_summary(tracker):
    """Format the tracked changes into a human-readable summary."""
    lines = ['\n--- DRY RUN SUMMARY ---']

    # Created — group by model
    created_by_model = {}
    created_ids = set()
    for model, rid, name in tracker['created']:
        created_by_model.setdefault(model, []).append(name)
        created_ids.add((model, rid))

    if created_by_model:
        lines.append('\nCreated:')
        for model, names in sorted(created_by_model.items()):
            lines.append(f'  {model}: {len(names)} record(s)')
            for n in names:
                lines.append(f'    + {n}')

    # Written — exclude records that were just created (ORM noise)
    written_by_model = {}
    for (model, rid), name in tracker['written'].items():
        if (model, rid) not in created_ids:
            written_by_model.setdefault(model, []).append(name)

    if written_by_model:
        lines.append('\nModified:')
        for model, names in sorted(written_by_model.items()):
            lines.append(f'  {model}: {len(names)} record(s)')
            for n in names:
                lines.append(f'    ~ {n}')

    # Deleted — group by model
    deleted_by_model = {}
    for model, rid, name in tracker['deleted']:
        deleted_by_model.setdefault(model, []).append(name)

    if deleted_by_model:
        lines.append('\nDeleted:')
        for model, names in sorted(deleted_by_model.items()):
            lines.append(f'  {model}: {len(names)} record(s)')
            for n in names:
                lines.append(f'    - {n}')

    if not created_by_model and not written_by_model and not deleted_by_model:
        lines.append('\nNo database changes detected.')

    lines.append('\nAll changes have been rolled back.')
    return '\n'.join(lines)


class ScriptScript(models.Model):
    _name = 'script.script'
    _description = 'Script'

    name = fields.Char(required=True)
    description = fields.Text()
    code = fields.Text(
        required=True,
        default='# Available: env, params, files, print\n',
    )
    text_params = fields.Text(string='Text Parameters', default='')
    file_param_ids = fields.One2many('script.file.param', 'script_id', string='File Parameters')
    execution_ids = fields.One2many('script.execution', 'script_id', string='Executions')
    execution_count = fields.Integer(compute='_compute_execution_count')
    dry_run = fields.Boolean(string='Dry Run', help='Execute the script but rollback all database changes. Log output is preserved.')
    timeout = fields.Integer(string='Timeout (s)', default=600, help='Maximum execution time in seconds. 0 = no limit.')
    active = fields.Boolean(default=True)

    @api.depends('execution_ids')
    def _compute_execution_count(self):
        data = self.env['script.execution']._read_group(
            [('script_id', 'in', self.ids)],
            groupby=['script_id'],
            aggregates=['__count'],
        )
        counts = {script.id: count for script, count in data}
        for rec in self:
            rec.execution_count = counts.get(rec.id, 0)

    def action_run(self):
        """Open the run wizard."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Run Script"),
            'res_model': 'script.run.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_script_id': self.id},
        }

    def action_view_executions(self):
        """Smart button: view executions for this script."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Executions"),
            'res_model': 'script.execution',
            'view_mode': 'list,form',
            'domain': [('script_id', '=', self.id)],
        }

    def _launch_execution(self, description=False):
        """Create execution record and launch background thread.

        In test mode, executes synchronously on the same cursor to avoid
        commit/rollback issues (same pattern as mail.mail).

        If self.dry_run is True, all database changes made by the script are
        rolled back via savepoint. Log output is still captured.

        Warning: in production mode this method commits the current
        transaction before spawning the background thread.  Do not call
        from within a larger uncommitted ORM workflow.
        """
        self.ensure_one()
        dry_run = self.dry_run
        timeout = max(self.timeout or 0, 0)

        # Snapshot file params
        file_lines = []
        file_data = {}
        for fp in self.file_param_ids:
            file_lines.append(f'{fp.name}: {fp.attachment_id.name}')
            file_data[fp.name] = fp.attachment_id.raw

        execution = self.env['script.execution'].create({
            'script_id': self.id,
            'script_name': self.name,
            'user_id': self.env.user.id,
            'description': description,
            'dry_run': dry_run,
            'state': 'running',
            'date_start': fields.Datetime.now(),
            'text_params': self.text_params or '',
            'file_params_display': '\n'.join(file_lines) if file_lines else '',
        })

        if modules.module.current_test:
            # Synchronous execution during tests — no commit, no thread
            self._execute_sync(execution, file_data, dry_run=dry_run)
        else:
            # Commit so the execution record is visible to the new thread
            self.env.cr.commit()

            thread = threading.Thread(
                target=self._execute_in_thread,
                args=(
                    execution.id,
                    self.code,
                    self.text_params or '',
                    file_data,
                    self.env.cr.dbname,
                    self.env.user.id,
                    dry_run,
                    timeout,
                ),
                daemon=True,
            )
            thread.start()

        return execution

    def _execute_sync(self, execution, file_data, dry_run=False):
        """Execute script synchronously (used in tests)."""
        stdout_capture = StringIO()
        t0 = time.perf_counter()
        custom_print = _make_print(stdout_capture)

        def _result(state, error_tb=''):
            execution.write({
                'state': state,
                'date_end': fields.Datetime.now(),
                'duration': round(time.perf_counter() - t0, 3),
                'log_output': stdout_capture.getvalue() or '',
                'error_output': error_tb,
            })

        exec_globals = self._build_exec_globals(self.env, custom_print, self.text_params or '', file_data)

        try:
            self._do_exec(self.code, exec_globals, self.env.cr, self.env, stdout_capture, dry_run)
            _result('success')
        except Exception:
            _result('error', traceback.format_exc())

    # Builtins allowed inside scripts. Excludes __import__, eval, exec,
    # compile, open, breakpoint — scripts get pre-imported modules instead.
    _SAFE_BUILTINS = {
        k: v for k, v in __builtins__.items()
        if k not in (
            '__import__', 'eval', 'exec', 'compile',
            'open', 'breakpoint', 'exit', 'quit',
            'globals', 'locals', 'vars', 'dir',
            'memoryview', '__build_class__',
        )
    } if isinstance(__builtins__, dict) else {
        k: getattr(__builtins__, k) for k in (
            'abs', 'all', 'any', 'bin', 'bool', 'bytes', 'callable',
            'chr', 'classmethod', 'complex', 'delattr', 'dict',
            'divmod', 'enumerate', 'filter', 'float', 'format',
            'frozenset', 'getattr', 'hasattr', 'hash', 'hex', 'id',
            'int', 'isinstance', 'issubclass', 'iter', 'len', 'list',
            'map', 'max', 'min', 'next', 'object', 'oct', 'ord',
            'pow', 'print', 'property', 'range', 'repr', 'reversed',
            'round', 'set', 'setattr', 'slice', 'sorted',
            'staticmethod', 'str', 'sum', 'super', 'tuple', 'type',
            'zip', 'True', 'False', 'None',
            'ValueError', 'TypeError', 'KeyError', 'IndexError',
            'AttributeError', 'RuntimeError', 'StopIteration',
            'Exception', 'BaseException', 'NotImplementedError',
            'ZeroDivisionError', 'OSError', 'IOError',
            'UnicodeDecodeError', 'UnicodeEncodeError',
        ) if hasattr(__builtins__, k)
    }

    @staticmethod
    def _build_exec_globals(env, custom_print, text_params, file_data):
        """Build the globals dict for exec()."""
        exec_globals = {
            '__builtins__': ScriptScript._SAFE_BUILTINS,
            'env': env,
            'params': text_params,
            'files': file_data,
            'print': custom_print,
            'datetime': __import__('datetime'),
            'json': __import__('json'),
            'csv': __import__('csv'),
            'io': __import__('io'),
            'base64': __import__('base64'),
            're': __import__('re'),
            'logging': __import__('logging'),
        }

        try:
            exec_globals['openpyxl'] = __import__('openpyxl')
        except ImportError:
            pass

        return exec_globals

    @staticmethod
    def _do_exec(code, exec_globals, cr, env, stdout_capture, dry_run):
        """Core exec logic shared by direct and timeout paths."""
        if dry_run:
            _install_dry_run_hooks()
            _dry_run_tracker.data = {'created': [], 'written': {}, 'deleted': []}
            cr.execute('SAVEPOINT dry_run_sp')
            try:
                exec(code, exec_globals)
            finally:
                tracker_data = _dry_run_tracker.data
                _dry_run_tracker.data = None
                _uninstall_dry_run_hooks()
                stdout_capture.write(_format_dry_run_summary(tracker_data))
                try:
                    cr.execute('ROLLBACK TO SAVEPOINT dry_run_sp')
                    cr.execute('RELEASE SAVEPOINT dry_run_sp')
                except Exception:
                    _logger.warning('Failed to clean up dry-run savepoint', exc_info=True)
                env.invalidate_all()
        else:
            exec(code, exec_globals)

    @staticmethod
    def _execute_in_thread(execution_id, code, text_params, file_data, db_name, user_id, dry_run=False, timeout=0):
        """Background thread: execute script code and update execution record."""
        stdout_capture = StringIO()
        t0 = time.perf_counter()
        custom_print = _make_print(stdout_capture)

        def _record_result(state, error_output=''):
            """Write execution result using a fresh cursor."""
            try:
                reg = Registry(db_name)
                with reg.cursor() as cr2:
                    env2 = api.Environment(cr2, user_id, {})
                    env2['script.execution'].browse(execution_id).write({
                        'state': state,
                        'date_end': fields.Datetime.now(),
                        'duration': round(time.perf_counter() - t0, 3),
                        'log_output': stdout_capture.getvalue() or '',
                        'error_output': error_output,
                    })
                    cr2.commit()
            except Exception:
                _logger.exception('Failed to record result for execution %s', execution_id)

        try:
            registry = Registry(db_name)
            with registry.cursor() as cr:
                env = api.Environment(cr, user_id, {})
                exec_globals = ScriptScript._build_exec_globals(env, custom_print, text_params, file_data)

                if timeout > 0:
                    # Get backend PID so we can cancel queries from outside
                    cr.execute("SELECT pg_backend_pid()")
                    backend_pid = cr.fetchone()[0]

                    exec_error = [None]  # None=success, str=traceback

                    def _run():
                        try:
                            ScriptScript._do_exec(code, exec_globals, cr, env, stdout_capture, dry_run)
                        except Exception:
                            exec_error[0] = traceback.format_exc()

                    sub = threading.Thread(target=_run, daemon=True)
                    sub.start()
                    sub.join(timeout=timeout)

                    if sub.is_alive():
                        # Timeout — cancel any running query via separate connection
                        try:
                            with registry.cursor() as cr_cancel:
                                cr_cancel.execute(
                                    "SELECT pg_cancel_backend(%s)", [backend_pid]
                                )
                        except Exception:
                            pass
                        # Raise TimeoutError in the sub-thread for pure-Python loops
                        _raise_timeout_in_thread(sub.ident)
                        sub.join(timeout=5)
                        _record_result(
                            'error',
                            f"Script execution timed out after {timeout}s",
                        )
                        return

                    if exec_error[0]:
                        _record_result('error', exec_error[0])
                        return
                else:
                    ScriptScript._do_exec(code, exec_globals, cr, env, stdout_capture, dry_run)

                # Success
                execution = env['script.execution'].browse(execution_id)
                execution.write({
                    'state': 'success',
                    'date_end': fields.Datetime.now(),
                    'duration': round(time.perf_counter() - t0, 3),
                    'log_output': stdout_capture.getvalue() or '',
                })
                cr.commit()

        except Exception:
            _logger.exception('Script execution %s failed', execution_id)
            _record_result('error', traceback.format_exc())
