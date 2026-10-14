from django.db import transaction
from django.utils import timezone
from .models import AccessEvent, AttendanceRecord, RFIDCredential

@transaction.atomic
def process_access_scan(*, device, card_uid, event_type, request_id=""):
    """Evaluate baseline RFID policy and write an event; no biometric or relay control."""
    now = timezone.now()
    credential = RFIDCredential.objects.select_related("person").filter(uid=card_uid).first()
    person = credential.person if credential else None
    if credential is None:
        decision, reason = AccessEvent.Decision.DENIED, "Unknown RFID credential"
    elif not credential.is_valid(now):
        decision, reason = AccessEvent.Decision.DENIED, "Credential or person inactive or outside validity period"
    else:
        decision, reason = AccessEvent.Decision.GRANTED, "Valid RFID credential; baseline RFID-only policy"
    event = AccessEvent.objects.create(device=device, person=person, card_uid=card_uid, event_type=event_type,
        decision=decision, reason=reason, metadata={"request_id": request_id} if request_id else {})
    attendance_recorded = False
    if decision == AccessEvent.Decision.GRANTED and person and event_type in (AccessEvent.EventType.ENTRY, AccessEvent.EventType.EXIT):
        AttendanceRecord.objects.create(person=person, event=event, attendance_date=timezone.localdate(now), event_type=event_type, recorded_at=now)
        attendance_recorded = True
    device.last_seen_at = now
    device.save(update_fields=["last_seen_at"])
    return event, attendance_recorded
