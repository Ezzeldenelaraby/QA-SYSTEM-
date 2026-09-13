from django.urls import path
from . import views

app_name = 'training'

urlpatterns = [
    path('', views.training_matrix_view, name='matrix'),
    path('list/', views.training_matrix_view, name='list'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('records/', views.record_list, name='record_list'),
    path('records/create/', views.record_create, name='record_create'),
]
