from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mail_telegram_bot_token = fields.Char(
        string=_("Telegram Bot Token"),
        help=_("Bot token from @BotFather. Used to send messages via Telegram Bot API."),
        config_parameter="mail_telegram.bot_token",
    )
    mail_telegram_default_chat_id = fields.Char(
        string=_("Default Chat ID"),
        help=_("Default Telegram chat/group ID. Modules can override per-record."),
        config_parameter="mail_telegram.default_chat_id",
    )
