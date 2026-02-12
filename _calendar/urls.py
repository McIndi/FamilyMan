from django.urls import path
from . import views

urlpatterns = [
    # Removed the URL mapping for event_list
    path('create/', views.event_create, name='event_create'),
    path('<int:pk>/update/', views.event_update, name='event_update'),
    path('<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('day/<int:year>/<int:month>/<int:day>/', views.day_view, name='day_view'),
    path('week/<int:year>/<int:month>/<int:day>/', views.week_view, name='week_view'),
    path('month/<int:year>/<int:month>/', views.month_view, name='month_view'),
]