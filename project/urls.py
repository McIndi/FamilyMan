from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('add-child/', views.add_child, name='add_child'),
    path('switch-family/', views.switch_family, name='switch_family'),
    path('family-dashboard/', views.family_dashboard, name='family_dashboard'),
    path('update-role/', views.update_role, name='update_role'),
]
