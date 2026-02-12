from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.merit_dashboard, name='merit_dashboard'),
    path('add_merit/', views.add_merit, name='add_merit'),
    path('add_demerit/', views.add_demerit, name='add_demerit'),
]