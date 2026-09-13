from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('search/', views.global_search, name='global_search'),
    path('scan-lookup/', views.scan_lookup, name='scan_lookup'),
    path('settings/', views.system_settings_view, name='system_settings'),
    path('settings/backup/create/', views.trigger_backup_view, name='trigger_backup'),
    path('settings/backup/download/<str:filename>/', views.download_backup_view, name='download_backup'),
    path('audit-trail/', views.audit_trail_view, name='audit_trail'),
]
