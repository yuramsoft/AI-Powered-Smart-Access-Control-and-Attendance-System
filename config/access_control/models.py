import hashlib
import secrets
from django.db import models
from django.utils import timezone

class Person(models.Model):
    class PersonType(models.TextChoices):
        STAFF = "STAFF", "Staff"
        STUDENT = "STUDENT", "Student"
        VISITOR = "VISITOR", "Visitor"
    person_code = models.CharField(max_length=64, unique=True)
    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    person_type = models.CharField(max_length=16, choices=PersonType.choices, default=PersonType.STAFF)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.person_code} — {self.full_name}"

class RFIDCredential(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="rfid_credentials")
    uid = models.CharField(max_length=32, unique=True, help_text="Normalized hexadecimal UID; not a secure secret.")
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def is_valid(self, at=None):
        at = at or timezone.now()
        return self.is_active and self.person.is_active and (self.valid_from is None or self.valid_from <= at) and (self.valid_until is None or self.valid_until >= at)
    def __str__(self): return f"{self.uid} → {self.person.person_code}"

class AccessDevice(models.Model):
    device_id = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=180, blank=True)
    token_hash = models.CharField(max_length=64, help_text="SHA-256 hex digest of device token.")
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def set_token(self, raw_token): self.token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    def authenticate(self, raw_token):
        if not self.is_active or not raw_token: return False
        supplied = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        return secrets.compare_digest(self.token_hash, supplied)
    def __str__(self): return f"{self.device_id} — {self.name}"

class AccessEvent(models.Model):
    class Decision(models.TextChoices):
        GRANTED = "GRANTED", "Granted"
        DENIED = "DENIED", "Denied"
    class EventType(models.TextChoices):
        ENTRY = "ENTRY", "Entry"
        EXIT = "EXIT", "Exit"
        ACCESS_ONLY = "ACCESS_ONLY", "Access only"
    device = models.ForeignKey(AccessDevice, on_delete=models.PROTECT, related_name="events")
    person = models.ForeignKey(Person, on_delete=models.PROTECT, null=True, blank=True, related_name="access_events")
    card_uid = models.CharField(max_length=32)
    event_type = models.CharField(max_length=16, choices=EventType.choices, default=EventType.ACCESS_ONLY)
    decision = models.CharField(max_length=8, choices=Decision.choices)
    reason = models.CharField(max_length=180)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return f"{self.created_at:%Y-%m-%d %H:%M:%S} {self.card_uid} {self.decision}"

class AttendanceRecord(models.Model):
    person = models.ForeignKey(Person, on_delete=models.PROTECT, related_name="attendance_records")
    event = models.OneToOneField(AccessEvent, on_delete=models.PROTECT, related_name="attendance")
    attendance_date = models.DateField(db_index=True)
    event_type = models.CharField(max_length=16, choices=AccessEvent.EventType.choices)
    recorded_at = models.DateTimeField(default=timezone.now)
    class Meta:
        ordering = ["-recorded_at"]
        indexes = [models.Index(fields=["person", "attendance_date"])]
    def __str__(self): return f"{self.person.person_code} — {self.attendance_date} — {self.event_type}"
