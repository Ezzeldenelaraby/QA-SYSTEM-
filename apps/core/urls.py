from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('search/', views.global_search, name='global_search'),
    path('settings/', views.system_settings_view, name='system_settings'),
    path('audit-trail/', views.audit_trail_view, name='audit_trail'),
]
