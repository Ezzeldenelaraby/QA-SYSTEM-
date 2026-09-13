from django.urls import path
from . import views

app_name = 'audits'

urlpatterns = [
    path('', views.audit_list, name='list'),
    path('create/', views.audit_create, name='create'),
    path('<int:audit_id>/', views.audit_detail, name='detail'),
    path('<int:audit_id>/edit/', views.audit_edit, name='edit'),
    path('<int:audit_id>/add-checklist/', views.audit_add_checklist_item, name='add_checklist'),
    path('<int:audit_id>/add-finding/', views.audit_add_finding, name='add_finding'),
    path('finding/<int:finding_id>/create-ncr/', views.audit_finding_create_ncr, name='finding_create_ncr'),
    path('finding/<int:finding_id>/create-action/', views.audit_finding_create_action, name='finding_create_action'),
]
