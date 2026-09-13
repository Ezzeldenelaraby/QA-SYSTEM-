from django.urls import path
from . import views

app_name = 'objectives'

urlpatterns = [
    path('', views.objective_list, name='list'),
    path('create/', views.objective_create, name='create'),
    path('<int:obj_id>/', views.objective_detail, name='detail'),
    path('<int:obj_id>/edit/', views.objective_edit, name='edit'),
    path('<int:obj_id>/add-measurement/', views.objective_add_measurement, name='add_measurement'),
]
