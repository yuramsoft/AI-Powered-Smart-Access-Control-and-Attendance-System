from django.contrib import admin
from .models import AccessDevice, AccessEvent, AttendanceRecord, Person, RFIDCredential

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("person_code", "full_name", "person_type", "is_active")
    search_fields = ("person_code", "full_name", "email")
    list_filter = ("person_type", "is_active")

@admin.register(RFIDCredential)
class RFIDCredentialAdmin(admin.ModelAdmin):
    list_display = ("uid", "person", "is_active", "valid_from", "valid_until")
    search_fields = ("uid", "person__person_code", "person__full_name")
    list_filter = ("is_active",)

@admin.register(AccessDevice)
class AccessDeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "location", "is_active", "last_seen_at")
    search_fields = ("device_id", "name", "location")
    list_filter = ("is_active",)

@admin.register(AccessEvent)
class AccessEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "device", "card_uid", "person", "decision", "reason", "event_type")
    search_fields = ("card_uid", "person__full_name", "device__device_id", "reason")
    list_filter = ("decision", "event_type", "device")
    readonly_fields = ("created_at",)

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("person", "attendance_date", "event_type", "recorded_at")
    search_fields = ("person__full_name", "person__person_code")
    list_filter = ("attendance_date", "event_type")
