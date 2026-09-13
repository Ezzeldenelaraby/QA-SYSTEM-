from django.urls import path
from . import views

app_name = 'ncr'

urlpatterns = [
    path('', views.ncr_list, name='list'),
    path('create/', views.ncr_create, name='create'),
    path('<int:ncr_id>/', views.ncr_detail, name='detail'),
    path('<int:ncr_id>/edit/', views.ncr_edit, name='edit'),
    path('<int:ncr_id>/five-whys/', views.ncr_save_five_whys, name='five_whys'),
    path('<int:ncr_id>/add-fishbone/', views.ncr_add_fishbone_cause, name='add_fishbone'),
    path('<int:ncr_id>/close/', views.ncr_close_view, name='close'),
    path('<int:ncr_id>/escalate-capa/', views.ncr_escalate_capa, name='escalate_capa'),
    path('<int:ncr_id>/red-tag/', views.ncr_print_red_tag, name='red_tag'),
]
