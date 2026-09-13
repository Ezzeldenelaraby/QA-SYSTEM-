from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='list'),
    path('create/', views.document_create, name='create'),
    path('<int:doc_id>/', views.document_detail, name='detail'),
    path('<int:doc_id>/edit/', views.document_edit, name='edit'),
    path('<int:doc_id>/submit-review/', views.document_submit_review, name='submit_review'),
    path('<int:doc_id>/approve/', views.document_approve, name='approve'),
    path('<int:doc_id>/reject/', views.document_reject, name='reject'),
    path('<int:doc_id>/new-revision/', views.document_new_revision, name='new_revision'),
    path('<int:doc_id>/mark-obsolete/', views.document_mark_obsolete, name='mark_obsolete'),
]
