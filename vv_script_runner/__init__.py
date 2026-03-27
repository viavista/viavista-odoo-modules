from . import models
from . import wizard


def _uninstall_hook(env):
    """Restore original BaseModel methods if dry-run hooks are still active."""
    from .models.script_script import _uninstall_dry_run_hooks
    _uninstall_dry_run_hooks()
