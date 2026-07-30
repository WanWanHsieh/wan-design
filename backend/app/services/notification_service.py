import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.models.order import Order

logger = logging.getLogger("notifications")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

SHIPPING_LABELS = {
    "family_mart": "好賣家(全家)",
    "seven_eleven": "賣貨便(7-11)",
    "address": "地址配送",
}


def _build_order_summary(order: Order) -> str:
    lines = [
        f"新訂單:{order.order_no}",
        f"收件人:{order.customer_name}({order.phone})",
        f"寄送方式:{SHIPPING_LABELS.get(order.shipping_method, order.shipping_method)}",
    ]
    if order.shipping_store_code:
        lines.append(f"店號:{order.shipping_store_code}")
    if order.shipping_address:
        lines.append(f"地址:{order.shipping_address}")
    lines.append(f"預期收到日期:{order.expected_delivery_date}")
    lines.append("")
    lines.append("訂購項目:")
    for item in order.items:
        detail = item.product_name_snapshot
        if item.material_name_snapshot:
            detail += f" × {item.material_name_snapshot}"
        lines.append(f"  - {detail} × {item.quantity} = NT$ {item.subtotal}")
    lines.append("")
    lines.append(f"總金額:NT$ {order.total_amount}")
    if order.notes:
        lines.append(f"備註:{order.notes}")
    return "\n".join(lines)


def notify_new_order(order: Order) -> None:
    summary = _build_order_summary(order)

    if not settings.smtp_configured:
        logger.info("新訂單通知 (未設定 SMTP,僅記錄於 log):\n%s", summary)
        return

    try:
        message = EmailMessage()
        message["Subject"] = f"【新訂單】{order.order_no} - {order.customer_name}"
        message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
        message["To"] = settings.NOTIFY_TO_EMAIL
        message.set_content(summary)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception:
        logger.exception("寄送新訂單通知信失敗,訂單編號:%s", order.order_no)
