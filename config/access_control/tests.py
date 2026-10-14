import hashlib
from django.test import TestCase
from rest_framework.test import APIClient
from .models import AccessDevice, AccessEvent, AttendanceRecord, Person, RFIDCredential

class AccessScanTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.token = "test-device-token-never-use-in-production"
        self.device = AccessDevice.objects.create(device_id="test-door", name="Test Door", token_hash=hashlib.sha256(self.token.encode()).hexdigest(), is_active=True)
        self.person = Person.objects.create(person_code="TEST001", full_name="Test Person", is_active=True)
        RFIDCredential.objects.create(person=self.person, uid="A1B2C3D4", is_active=True)
        self.url = "/api/v1/access/scan/"
    def post_scan(self, uid="A1B2C3D4", event_type="ENTRY", token=None):
        self.client.credentials(HTTP_X_DEVICE_ID="test-door", HTTP_X_DEVICE_TOKEN=token or self.token)
        return self.client.post(self.url, {"device_id":"test-door", "card_uid":uid, "event_type":event_type}, format="json")
    def test_valid_entry_is_granted_and_records_attendance(self):
        response = self.post_scan()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["decision"], AccessEvent.Decision.GRANTED)
        self.assertTrue(response.data["attendance_recorded"])
        self.assertEqual(AttendanceRecord.objects.count(), 1)
    def test_unknown_card_is_denied_and_audited(self):
        response = self.post_scan(uid="DEADBEEF")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["decision"], AccessEvent.Decision.DENIED)
        self.assertEqual(AccessEvent.objects.count(), 1)
        self.assertEqual(AttendanceRecord.objects.count(), 0)
    def test_bad_device_token_is_rejected(self):
        response = self.post_scan(token="wrong-token")
        self.assertEqual(response.status_code, 401)
    def test_invalid_card_uid_is_rejected(self):
        response = self.post_scan(uid="NOT-HEX")
        self.assertEqual(response.status_code, 400)
    def test_disabled_person_is_denied(self):
        self.person.is_active = False
        self.person.save(update_fields=["is_active"])
        response = self.post_scan()
        self.assertEqual(response.data["decision"], AccessEvent.Decision.DENIED)
