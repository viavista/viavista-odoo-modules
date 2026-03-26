from . import models
from . import wizard


def _uninstall_hook(env):
    """Restore original BaseModel methods patched by dry-run hooks."""
    from odoo.orm.models import BaseModel
    if getattr(BaseModel, '_vv_dry_run_hooks', False):
        BaseModel.create = BaseModel._vv_orig_create
        BaseModel.write = BaseModel._vv_orig_write
        BaseModel.unlink = BaseModel._vv_orig_unlink
        del BaseModel._vv_dry_run_hooks
        del BaseModel._vv_orig_create
        del BaseModel._vv_orig_write
        del BaseModel._vv_orig_unlink
