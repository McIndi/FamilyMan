from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .views import ItemViewSet, past_items

# Register the API routes using a DRF router.
router = DefaultRouter()
router.register(r'api/shoppinglist', ItemViewSet, basename='item')

# Define URL patterns for the shoppinglist app.
urlpatterns = [
    path('items/', views.item_list, name='item_list'),  # List all items.
    path('create/', views.item_create, name='item_create'),  # Create a new item.
    path('<int:pk>/update/', views.item_update, name='item_update'),  # Update an item.
    path('<int:pk>/delete/', views.item_delete, name='item_delete'),  # Delete an item.
    path('past-items/', past_items, name='past_items'),  # List all obtained items.
] + router.urls  # Include API routes.
