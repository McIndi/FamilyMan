from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    def validate_attendees(self, attendees):
        request = self.context.get('request')
        family = getattr(request, 'current_family', None) if request else None
        if not family:
            raise serializers.ValidationError("No family context set.")
        allowed_ids = set(family.members.values_list('id', flat=True))
        for attendee in attendees:
            if attendee.id not in allowed_ids:
                raise serializers.ValidationError("All attendees must belong to the current family.")
        return attendees

    class Meta:
        model = Event
        fields = ['id', 'title', 'text', 'when', 'attendees', 'host', 'duration', 'repeat']
        read_only_fields = ['host']