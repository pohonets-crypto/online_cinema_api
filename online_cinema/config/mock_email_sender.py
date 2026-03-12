import logging

from online_cinema.notifications import EmailSenderInterface

logger = logging.getLogger(__name__)


class MockEmailSender(EmailSenderInterface):
    """Stub email sender for development/testing. Logs instead of sending."""

    async def send_activation_email(self, email: str, activation_link: str) -> None:
        logger.info(
            "[MOCK EMAIL] Activation email to %s | link: %s", email, activation_link
        )

    async def send_activation_complete_email(self, email: str, login_link: str) -> None:
        logger.info(
            "[MOCK EMAIL] Activation complete email to %s | link: %s", email, login_link
        )

    async def send_password_reset_email(self, email: str, reset_link: str) -> None:
        logger.info(
            "[MOCK EMAIL] Password reset email to %s | link: %s", email, reset_link
        )

    async def send_password_reset_complete_email(
        self, email: str, login_link: str
    ) -> None:
        logger.info(
            "[MOCK EMAIL] Password reset complete email to %s | link: %s",
            email,
            login_link,
        )
