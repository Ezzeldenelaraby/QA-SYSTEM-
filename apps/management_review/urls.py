from django.urls import path
from . import views

app_name = 'management_review'

urlpatterns = [
    path('', views.meeting_list, name='list'),
    path('create/', views.meeting_create, name='create'),
    path('<int:pk>/', views.meeting_detail, name='detail'),
    path('<int:pk>/edit/', views.meeting_update, name='edit'),
    path('<int:pk>/approve/', views.meeting_approve_minutes, name='approve_minutes'),
]
