"""
URL configuration for familyman project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('shoppinglist/', include('shoppinglist.urls')),  # Include shoppinglist app URLs
    path('calendar/', include('_calendar.urls')),  # Include calendar app URLs
    path('mail/', include('mail.urls')),  # Include mail app URLs
    path('merits/', include('merits.urls')),  # Include mail app URLs
    path('cash/', include('cash.urls')),  # Include cash app URLs
    path('', include('project.urls')),  # Include project app URLs
]

urlpatterns += [
    path('accounts/', include('allauth.urls')),  # Add allauth URLs
]
