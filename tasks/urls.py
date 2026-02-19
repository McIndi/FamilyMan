from django.urls import path

from . import views


urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('create/', views.task_create, name='task_create'),
    path('<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('<int:task_id>/complete/', views.task_complete, name='task_complete'),
    path('<int:task_id>/reopen/', views.task_reopen, name='task_reopen'),
]
