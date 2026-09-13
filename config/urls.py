from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('departments/', include('apps.departments.urls', namespace='departments')),
    path('processes/', include('apps.processes.urls', namespace='processes')),
    path('documents/', include('apps.documents.urls', namespace='documents')),
    path('risks/', include('apps.risks.urls', namespace='risks')),
    path('objectives/', include('apps.objectives.urls', namespace='objectives')),
    path('ncr/', include('apps.ncr.urls', namespace='ncr')),
    path('capa/', include('apps.capa.urls', namespace='capa')),
    path('actions/', include('apps.actions.urls', namespace='actions')),
    path('audits/', include('apps.audits.urls', namespace='audits')),
    path('inspections/', include('apps.inspections.urls', namespace='inspections')),
    path('calibration/', include('apps.calibration.urls', namespace='calibration')),
    path('training/', include('apps.training.urls', namespace='training')),
    path('management-review/', include('apps.management_review.urls', namespace='management_review')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
    path('core/', include('apps.core.urls', namespace='core')),
    path('api/v1/', include('apps.api.urls', namespace='api')),
    path('health/', health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = 'apps.core.views.custom_permission_denied'
handler404 = 'apps.core.views.custom_page_not_found'
handler500 = 'apps.core.views.custom_server_error'
