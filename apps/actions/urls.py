from django.urls import path
from . import views

app_name = 'actions'

urlpatterns = [
    path('', views.action_list, name='list'),
    path('my-actions/', views.my_actions, name='my_actions'),
    path('create/', views.action_create, name='create'),
    path('<int:action_id>/', views.action_detail, name='detail'),
    path('<int:action_id>/edit/', views.action_edit, name='edit'),
    path('<int:action_id>/complete/', views.action_complete, name='complete'),
    path('<int:action_id>/verify/', views.action_verify, name='verify'),
]
