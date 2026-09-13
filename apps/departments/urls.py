from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.department_list, name='list'),
    path('create/', views.department_create, name='create'),
    path('<int:dept_id>/edit/', views.department_edit, name='edit'),
]
