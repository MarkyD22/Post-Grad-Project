from django.test import TestCase
from django.contrib.auth.models import User
from myapp.models import Equipment, UserProfile
from datetime import date, timedelta

class EquipmentModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.equipment = Equipment.objects.create(
            Machine_ID='TEST001',
            Machine_Name='Test CNC Machine',
            Machine_Type='cnc_machine',
            Machine_Location='Test Floor A',
            Last_Maintenance_Date=date.today() - timedelta(days=30),
            Last_Calibration_Date=date.today() - timedelta(days=60)
        )
    
    def test_equipment_creation(self):
        """Test equipment is created correctly"""
        self.assertEqual(self.equipment.Machine_ID, 'TEST001')
        self.assertEqual(self.equipment.Machine_Name, 'Test CNC Machine')
    
    def test_maintenance_status_calculation(self):
        """Test maintenance status logic"""
        # Test overdue equipment (older than 90 days)
        self.equipment.Last_Maintenance_Date = date.today() - timedelta(days=100)
        self.equipment.save()
        self.assertEqual(self.equipment.maintenance_status, 'overdue')
    
    def test_next_maintenance_due_calculation(self):
        """Test next maintenance date calculation"""
        expected_date = self.equipment.Last_Maintenance_Date + timedelta(days=90)
        self.assertEqual(self.equipment.next_maintenance_due, expected_date)