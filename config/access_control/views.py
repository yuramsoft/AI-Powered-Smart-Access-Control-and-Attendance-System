from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from .models import AccessDevice
from .serializers import AccessScanSerializer
from .services import process_access_scan

@api_view(["GET"])
def health(request):
    return Response({"status": "ok", "service": "smart-access-control"})

@api_view(["POST"])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def access_scan(request):
    device_id = request.headers.get("X-Device-ID", "")
    raw_token = request.headers.get("X-Device-Token", "")
    if not device_id or not raw_token:
        return Response({"detail": "Device authentication required."}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        device = AccessDevice.objects.get(device_id=device_id)
    except AccessDevice.DoesNotExist:
        return Response({"detail": "Invalid device credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    if not device.authenticate(raw_token):
        return Response({"detail": "Invalid device credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    payload = request.data.copy()
    payload["device_id"] = device_id
    serializer = AccessScanSerializer(data=payload)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    event, attendance_recorded = process_access_scan(device=device, card_uid=data["card_uid"], event_type=data["event_type"], request_id=data.get("request_id", ""))
    return Response({"event_id": event.id, "decision": event.decision, "reason": event.reason,
        "attendance_recorded": attendance_recorded, "relay_authorized": False,
        "note": "Physical actuation is disabled in this starter implementation."}, status=status.HTTP_200_OK)
