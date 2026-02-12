from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),
    path('compose/', views.compose_message, name='compose_message'),
    path('message/<int:pk>/delete/', views.delete_message, name='delete_message'),
    path('message/<int:pk>/confirm_delete/', views.confirm_delete_message, name='confirm_delete_message'),
    path('message/<int:pk>/edit/', views.edit_message, name='edit_message'),
    path('message/<int:pk>/reply/', views.reply_message, name='reply_message'),
]