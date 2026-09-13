from .models import AuditLog
from .middleware import get_current_user

def log_audit(user=None, action='UPDATE', module='', record_id='', record_name='', old_value='', new_value='', notes=''):
    """Helper to record audit trail events."""
    if not user:
        user = get_current_user()
    try:
        AuditLog.objects.create(
            user=user if getattr(user, 'is_authenticated', False) else None,
            action=action,
            module=module,
            record_id=str(record_id),
            record_name=str(record_name)[:255],
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            notes=str(notes) if notes else None,
        )
    except Exception as e:
        # Don't fail primary business transaction if audit log logging fails
        print(f"Error logging audit: {e}")


def generate_qr_code_base64(data_text):
    """Generate a base64 encoded data URI PNG for a given text or URL."""
    import base64
    from io import BytesIO
    import qrcode

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(data_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a365d", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{b64}"

