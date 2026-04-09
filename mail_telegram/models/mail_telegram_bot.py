import logging

import requests

from odoo import _, api, models

_logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot%s/sendMessage"
SEND_TIMEOUT = 10


class MailTelegramBot(models.AbstractModel):
    """Service model for sending Telegram messages.

    Usage from any module:
        self.env["mail.telegram.bot"].send_message(chat_id, "Hello!")
        self.env["mail.telegram.bot"].send_html(chat_id, "<b>Bold</b>")
    """

    _name = "mail.telegram.bot"
    _description = "Telegram Bot Service"

    @api.model
    def _get_bot_token(self):
        """Read bot token from system parameters."""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("mail_telegram.bot_token", "")
        )

    @api.model
    def send_message(self, chat_id, text, parse_mode=None):
        """Send a plain text message to a Telegram chat.

        Args:
            chat_id: Telegram chat/group ID (string or int)
            text: Message text
            parse_mode: Optional ("HTML" or "Markdown"). Default: no formatting.

        Returns:
            True if sent successfully, False otherwise.
        """
        token = self._get_bot_token()
        if not token:
            _logger.debug("Telegram bot token not configured, skipping")
            return False

        if not chat_id:
            _logger.debug("No chat_id provided, skipping")
            return False

        data = {
            "chat_id": str(chat_id),
            "text": text,
        }
        if parse_mode:
            data["parse_mode"] = parse_mode

        try:
            resp = requests.post(
                TELEGRAM_API_URL % token,
                data=data,
                timeout=SEND_TIMEOUT,
            )
            if resp.status_code != 200:
                _logger.warning(
                    "Telegram API returned %d: %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return False
            return True
        except requests.RequestException:
            _logger.warning("Failed to send Telegram message to %s", chat_id)
            return False

    @api.model
    def send_html(self, chat_id, html_text):
        """Send an HTML-formatted message to a Telegram chat."""
        return self.send_message(chat_id, html_text, parse_mode="HTML")
