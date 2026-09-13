import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

def send_qms_email(subject: str, template_name: str, context: dict, recipient_list: list[str]) -> bool:
    """
    Renders and dispatches branded QMS HTML emails with plain-text fallback.
    Catches errors gracefully to guarantee zero downtime or blocked requests.
    """
    if not recipient_list:
        logger.warning("send_qms_email called with empty recipient list.")
        return False

    # Filter out empty or None emails
    valid_recipients = [email for email in recipient_list if email and '@' in email]
    if not valid_recipients:
        logger.info(f"No valid email addresses found in {recipient_list}.")
        return False

    # Augment context with standard company/platform details
    context = dict(context or {})
    context.setdefault('platform_name', 'Industrial QMS Hub')
    context.setdefault('system_url', getattr(settings, 'SYSTEM_BASE_URL', 'http://127.0.0.1:8000'))

    try:
        html_content = render_to_string(template_name, context)
        text_content = strip_tags(html_content)

        msg = EmailMultiAlternatives(
            subject=f"[QMS Hub] {subject}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=valid_recipients,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)
        logger.info(f"Email sent successfully: '{subject}' to {valid_recipients}")
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch QMS email '{subject}' to {valid_recipients}: {e}")
        return False
