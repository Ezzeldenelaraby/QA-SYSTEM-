from .models import Notification

def notifications_context(request):
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }
    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False)
    return {
        'unread_notifications_count': unread_qs.count(),
        'recent_notifications': Notification.objects.filter(recipient=request.user)[:5],
    }
