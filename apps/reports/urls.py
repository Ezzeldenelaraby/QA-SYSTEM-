from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_index, name='index'),
    path('export/', views.export_dataset, name='export'),
    path('import/', views.bulk_import_view, name='bulk_import'),
    path('import/template/<str:model_type>/', views.download_import_template, name='download_template'),
]
