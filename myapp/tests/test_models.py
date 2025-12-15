
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta
from django.contrib.auth.models import User
from myapp.models import Equipment, UserProfile  # Adjust import path as needed


class EquipmentModelTest(TestCase):
    """Test cases for Equipment model"""
    
    def setUp(self):
        """Set up test data before each test method"""
        self.equipment_data = {
            'Machine_ID': 'EQ001',
            'Machine_Name': 'CNC Machine Alpha',
            'Machine_Type': 'CNC',
            'Machine_Location': 'Factory Floor A',
            'Last_Calibration_Date': date.today() - timedelta(days=30),
            'Last_Maintenance_Date': date.today() - timedelta(days=15)
        }
    
    def test_equipment_creation(self):
        """Test creating an equipment instance"""
        equipment = Equipment.objects.create(**self.equipment_data)
        
        self.assertEqual(equipment.Machine_ID, 'EQ001')
        self.assertEqual(equipment.Machine_Name, 'CNC Machine Alpha')
        self.assertEqual(equipment.Machine_Type, 'CNC')
        self.assertEqual(equipment.Machine_Location, 'Factory Floor A')
        self.assertIsNotNone(equipment.Last_Calibration_Date)
        self.assertIsNotNone(equipment.Last_Maintenance_Date)
    
    def test_equipment_string_representation(self):
        """Test the string representation of equipment"""
        equipment = Equipment.objects.create(**self.equipment_data)
        expected_str = f"{equipment.Machine_ID} - {equipment.Machine_Name}"
        self.assertEqual(str(equipment), expected_str)
    
    def test_machine_id_uniqueness(self):
        """Test that Machine_ID must be unique"""
        Equipment.objects.create(**self.equipment_data)
        
        # Try to create another equipment with same Machine_ID
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(**self.equipment_data)
    
    def test_machine_id_required(self):
        """Test that Machine_ID is required"""
        data = self.equipment_data.copy()
        data.pop('Machine_ID')
        
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(**data)
    
    def test_machine_name_required(self):
        """Test that Machine_Name is required"""
        data = self.equipment_data.copy()
        data.pop('Machine_Name')
        
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(**data)
    
    def test_date_fields_can_be_updated(self):
        """Test that Last_Calibration_Date and Last_Maintenance_Date can be updated"""
        equipment = Equipment.objects.create(**self.equipment_data)
        
        new_cal_date = date.today()
        new_maint_date = date.today()
        
        equipment.Last_Calibration_Date = new_cal_date
        equipment.Last_Maintenance_Date = new_maint_date
        equipment.save()
        
        equipment.refresh_from_db()
        self.assertEqual(equipment.Last_Calibration_Date, new_cal_date)
        self.assertEqual(equipment.Last_Maintenance_Date, new_maint_date)
    
    def test_equipment_search_by_name(self):
        """Test searching equipment by name"""
        Equipment.objects.create(**self.equipment_data)
        
        found_equipment = Equipment.objects.filter(Machine_Name__icontains='CNC')
        self.assertEqual(found_equipment.count(), 1)
        self.assertEqual(found_equipment.first().Machine_ID, 'EQ001')
    
    def test_equipment_search_by_type(self):
        """Test searching equipment by type"""
        Equipment.objects.create(**self.equipment_data)
        
        found_equipment = Equipment.objects.filter(Machine_Type='CNC')
        self.assertEqual(found_equipment.count(), 1)
    
    def test_equipment_search_by_location(self):
        """Test searching equipment by location"""
        Equipment.objects.create(**self.equipment_data)
        
        found_equipment = Equipment.objects.filter(Machine_Location__icontains='Floor A')
        self.assertEqual(found_equipment.count(), 1)
    
    def test_multiple_equipment_creation(self):
        """Test creating multiple equipment instances"""
        equipment1 = Equipment.objects.create(**self.equipment_data)
        
        equipment2_data = self.equipment_data.copy()
        equipment2_data.update({
            'Machine_ID': 'EQ002',
            'Machine_Name': 'Lathe Machine Beta',
            'Machine_Type': 'Lathe'
        })
        
        equipment2 = Equipment.objects.create(**equipment2_data)
        
        self.assertEqual(Equipment.objects.count(), 2)
        self.assertNotEqual(equipment1.Machine_ID, equipment2.Machine_ID)


class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model (custom user roles)"""
    
    def setUp(self):
        """Set up test data before each test method"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
    
    def test_user_profile_creation(self):
        """Test creating a user with profile"""
        user = User.objects.create_user(**self.user_data)
        profile = UserProfile.objects.create(
            user=user,
            role='Quality',
            employee_id='EMP001'
        )
        
        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.role, 'Quality')
        self.assertEqual(profile.employee_id, 'EMP001')
    
    def test_user_role_choices(self):
        """Test that only valid roles can be assigned"""
        user = User.objects.create_user(**self.user_data)
        
        valid_roles = ['Administrator', 'Maintenance', 'Quality']
        
        for role in valid_roles:
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                employee_id=f'EMP{role[:3].upper()}'
            )
            self.assertEqual(profile.role, role)
            profile.delete()  # Clean up for next iteration
    
    def test_user_profile_string_representation(self):
        """Test string representation of user profile"""
        user = User.objects.create_user(**self.user_data)
        profile = UserProfile.objects.create(
            user=user,
            role='Administrator',
            employee_id='EMP001'
        )
        
        expected_str = f"{user.username} - Administrator"
        self.assertEqual(str(profile), expected_str)
    
    def test_one_to_one_relationship(self):
        """Test that User and UserProfile have one-to-one relationship"""
        user = User.objects.create_user(**self.user_data)
        profile = UserProfile.objects.create(
            user=user,
            role='Maintenance',
            employee_id='EMP002'
        )
        
        # Test accessing profile from user
        self.assertEqual(user.userprofile, profile)
        
        # Test accessing user from profile
        self.assertEqual(profile.user, user)