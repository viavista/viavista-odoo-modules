import traceback

from werkzeug.exceptions import HTTPException

import odoo
from odoo import models
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    RedirectWarning,
    UserError,
    ValidationError,
)
from odoo.http import request

# Exceptions caused by normal user actions — not real server errors
_USER_EXCEPTIONS = (
    AccessDenied,
    AccessError,
    MissingError,
    RedirectWarning,
    UserError,
    ValidationError,
    HTTPException,
)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _handle_error(cls, exception):
        if not isinstance(exception, _USER_EXCEPTIONS):
            cls._log_rpc_error(exception)
        return super()._handle_error(exception)

    @classmethod
    def _log_rpc_error(cls, exception):
        """Write RPC error into ir.logging so it shows in Monitoring.

        Uses a separate DB connection because the main transaction
        is already rolled back when _handle_error is called.
        """
        try:
            tb_lines = traceback.format_exception(exception)
            message = "".join(tb_lines)

            # Extract location from the deepest frame in traceback
            tb = exception.__traceback__
            path = func = ""
            line = "0"
            while tb and tb.tb_next:
                tb = tb.tb_next
            if tb:
                frame = tb.tb_frame
                path = frame.f_code.co_filename
                func = frame.f_code.co_name
                line = str(tb.tb_lineno)

            dbname = request.db if request and request.db else ""
            uid = request.session.uid if request and request.session else None

            # The main cursor is dead after transaction.reset(),
            # so open a dedicated connection for the INSERT.
            db = odoo.sql_db.db_connect(dbname)
            with db.cursor() as cr:
                cr.execute(
                    """
                    INSERT INTO ir_logging
                        (create_date, write_date, create_uid, write_uid,
                         name, type, dbname, level, message, path, func, line)
                    VALUES
                        (NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC',
                         %s, %s,
                         %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uid,
                        uid,
                        "viavista.rpc.error",
                        "server",
                        dbname,
                        "ERROR",
                        message,
                        path,
                        func,
                        line,
                    ),
                )
        except Exception:
            # Never let logging break the error response
            pass
