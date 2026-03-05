import logging
import time

from app.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.email.send_order_confirmation")
def send_order_confirmation(order_id: str, user_email: str) -> None:
    logger.info(
        "task_start send_order_confirmation order_id=%s user_email=%s",
        order_id,
        user_email,
    )
    logger.info(
        "Sending order confirmation to %s for order %s",
        user_email,
        order_id,
    )
    time.sleep(3)
    logger.info(
        "task_end send_order_confirmation order_id=%s user_email=%s",
        order_id,
        user_email,
    )


@celery_app.task(name="app.tasks.email.send_status_update")
def send_status_update(order_id: str, user_email: str, status: str) -> None:
    logger.info(
        "task_start send_status_update order_id=%s user_email=%s status=%s",
        order_id,
        user_email,
        status,
    )
    logger.info(
        "Sending order status update to %s for order %s with status %s",
        user_email,
        order_id,
        status,
    )
    time.sleep(3)
    logger.info(
        "task_end send_status_update order_id=%s user_email=%s status=%s",
        order_id,
        user_email,
        status,
    )
