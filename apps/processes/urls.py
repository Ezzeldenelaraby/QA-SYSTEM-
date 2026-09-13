from django.urls import path
from . import views

app_name = 'processes'

urlpatterns = [
    path('', views.process_list, name='list'),
    path('create/', views.process_create, name='create'),
    path('<int:process_id>/', views.process_detail, name='detail'),
    path('<int:process_id>/edit/', views.process_edit, name='edit'),
]
