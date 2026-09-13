from django.urls import path
from . import views

app_name = 'calibration'

urlpatterns = [
    path('', views.calibration_list, name='list'),
    path('create/', views.calibration_create, name='create'),
    path('<int:eq_id>/', views.calibration_detail, name='detail'),
    path('<int:eq_id>/edit/', views.calibration_edit, name='edit'),
    path('<int:eq_id>/sticker/', views.equipment_sticker, name='sticker'),
]
