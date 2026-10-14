import re
from rest_framework import serializers
from .models import AccessEvent

class AccessScanSerializer(serializers.Serializer):
    device_id = serializers.SlugField(max_length=80)
    card_uid = serializers.CharField(max_length=32)
    event_type = serializers.ChoiceField(choices=AccessEvent.EventType.choices, default=AccessEvent.EventType.ACCESS_ONLY)
    request_id = serializers.CharField(max_length=80, required=False, allow_blank=False)
    def validate_card_uid(self, value):
        normalized = value.replace(":", "").replace("-", "").replace(" ", "").upper()
        if not re.fullmatch(r"[0-9A-F]{4,32}", normalized):
            raise serializers.ValidationError("Card UID must contain 4–32 hexadecimal characters.")
        return normalized
