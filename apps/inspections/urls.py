from django.urls import path
from . import views

app_name = 'inspections'

urlpatterns = [
    path('', views.inspection_list, name='list'),
    path('create/', views.inspection_create, name='create'),
    path('spc/', views.spc_analysis_view, name='spc'),
    path('<int:insp_id>/', views.inspection_detail, name='detail'),
    path('<int:insp_id>/edit/', views.inspection_edit, name='edit'),
    path('<int:insp_id>/add-item/', views.inspection_add_item, name='add_item'),
    path('<int:insp_id>/create-ncr/', views.inspection_create_ncr, name='create_ncr'),
]
