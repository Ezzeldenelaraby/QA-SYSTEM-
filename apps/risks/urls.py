from django.urls import path
from . import views

app_name = 'risks'

urlpatterns = [
    path('', views.risk_list, name='list'),
    path('matrix/', views.risk_matrix_view, name='matrix'),
    path('create/', views.risk_create, name='create'),
    path('<int:risk_id>/', views.risk_detail, name='detail'),
    path('<int:risk_id>/edit/', views.risk_edit, name='edit'),
]
