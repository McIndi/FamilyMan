from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    """
    Serializer for the Item model, used in the API.
    """
    class Meta:
        model = Item
        fields = ['id', 'text', 'kind', 'obtained']  # Include the 'obtained' field in the serializer.
