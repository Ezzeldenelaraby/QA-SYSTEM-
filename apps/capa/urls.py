from django.urls import path
from . import views

app_name = 'capa'

urlpatterns = [
    path('', views.capa_list, name='list'),
    path('create/', views.capa_create, name='create'),
    path('<int:capa_id>/', views.capa_detail, name='detail'),
    path('<int:capa_id>/edit/', views.capa_edit, name='edit'),
    path('<int:capa_id>/close/', views.capa_close, name='close'),
    path('<int:capa_id>/8d-pdf/', views.capa_8d_pdf, name='pdf_8d'),
]
