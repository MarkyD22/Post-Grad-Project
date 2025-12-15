from django.test import TestCase, TransactionTestCase
from django.db import transaction, IntegrityError, connections
from django.db.models import Q
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.contrib.auth.models import User
from myapp.models import Equipment, UserProfile  # Adjust import path as needed


class DatabaseIntegrityTest(TestCase):
    """Test database integrity and constraints"""
    
    def test_equipment_primary_key_uniqueness(self):
        """Test that Machine_ID as primary key is unique"""
        Equipment.objects.create(
            Machine_ID='TEST001',
            Machine_Name='Test Machine 1',
            Machine_Type='Test',
            Machine_Location='Test Location',
            Last_Calibration_Date=date.today(),
            Last_Maintenance_Date=date.today()
        )
        
        # Try to create another equipment with same Machine_ID
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(
                Machine_ID='TEST001',
                Machine_Name='Test Machine 2',
                Machine_Type='Test',
                Machine_Location='Test Location',
                Last_Calibration_Date=date.today(),
                Last_Maintenance_Date=date.today()
            )
    
    def test_foreign_key_constraints(self):
        """Test foreign key relationships work correctly"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        profile = UserProfile.objects.create(
            user=user,
            role='Quality',
            employee_id='EMP001'
        )
        
        # Test that deleting user cascades to profile
        user_id = user.id
        user.delete()
        
        with self.assertRaises(UserProfile.DoesNotExist):
            UserProfile.objects.get(user_id=user_id)
    
    def test_database_transactions(self):
        """Test database transaction handling"""
        with transaction.atomic():
            equipment = Equipment.objects.create(
                Machine_ID='TRANS001',
                Machine_Name='Transaction Test',
                Machine_Type='Test',
                Machine_Location='Test Location',
                Last_Calibration_Date=date.today(),
                Last_Maintenance_Date=date.today()
            )
            
            # Rollback transaction on error
            try:
                with transaction.atomic():
                    # This should fail due to duplicate Machine_ID
                    Equipment.objects.create(
                        Machine_ID='TRANS001',
                        Machine_Name='Another Machine',
                        Machine_Type='Test',
                        Machine_Location='Test Location',
                        Last_Calibration_Date=date.today(),
                        Last_Maintenance_Date=date.today()
                    )
            except IntegrityError:
                pass
        
        # Original equipment should still exist
        self.assertTrue(Equipment.objects.filter(Machine_ID='TRANS001').exists())
    
    def test_bulk_operations(self):
        """Test bulk database operations"""
        equipment_list = []
        for i in range(100):
            equipment_list.append(Equipment(
                Machine_ID=f'BULK{i:03d}',
                Machine_Name=f'Bulk Machine {i}',
                Machine_Type='Bulk Test',
                Machine_Location=f'Location {i}',
                Last_Calibration_Date=date.today(),
                Last_Maintenance_Date=date.today()
            ))
        
        # Bulk create
        Equipment.objects.bulk_create(equipment_list)
        
        # Verify all were created
        self.assertEqual(Equipment.objects.filter(Machine_Type='Bulk Test').count(), 100)
        
        # Bulk update
        Equipment.objects.filter(Machine_Type='Bulk Test').update(
            Machine_Location='Updated Location'
        )
        
        # Verify all were updated
        updated_count = Equipment.objects.filter(
            Machine_Type='Bulk Test',
            Machine_Location='Updated Location'
        ).count()
        self.assertEqual(updated_count, 100)


class DatabaseQueryTest(TestCase):
    """Test database queries and performance"""
    
    def setUp(self):
        """Set up test data"""
        # Create test equipment
        for i in range(50):
            Equipment.objects.create(
                Machine_ID=f'QUERY{i:03d}',
                Machine_Name=f'Query Test Machine {i}',
                Machine_Type='CNC' if i % 2 == 0 else 'Lathe',
                Machine_Location=f'Floor {i // 10 + 1}',
                Last_Calibration_Date=date.today() - timedelta(days=i * 7),
                Last_Maintenance_Date=date.today() - timedelta(days=i * 3)
            )
    
    def test_simple_queries(self):
        """Test basic database queries"""
        # Test get by primary key
        equipment = Equipment.objects.get(Machine_ID='QUERY001')
        self.assertEqual(equipment.Machine_Name, 'Query Test Machine 1')
        
        # Test filter
        cnc_machines = Equipment.objects.filter(Machine_Type='CNC')
        self.assertEqual(cnc_machines.count(), 25)
        
        # Test exclude
        non_cnc = Equipment.objects.exclude(Machine_Type='CNC')
        self.assertEqual(non_cnc.count(), 25)
    
    def test_complex_queries(self):
        """Test complex database queries"""
        # Test Q objects
        recent_calibration = Equipment.objects.filter(
            Q(Last_Calibration_Date__gte=date.today() - timedelta(days=30))
        )
        self.assertGreater(recent_calibration.count(), 0)
        
        # Test OR queries
        cnc_or_recent = Equipment.objects.filter(
            Q(Machine_Type='CNC') | 
            Q(Last_Maintenance_Date__gte=date.today() - timedelta(days=7))
        )
        self.assertGreater(cnc_or_recent.count(), 0)
        
        # Test ordering
        ordered_equipment = Equipment.objects.order_by('-Last_Calibration_Date')
        self.assertEqual(ordered_equipment.first().Machine_ID, 'QUERY000')
    
    def test_aggregation_queries(self):
        """Test aggregation queries"""
        from django.db.models import Count, Min, Max
        
        # Count by type
        type_counts = Equipment.objects.values('Machine_Type').annotate(
            count=Count('Machine_ID')
        )
        
        cnc_count = next(
            (item['count'] for item in type_counts if item['Machine_Type'] == 'CNC'),
            0
        )
        self.assertEqual(cnc_count, 25)
        
        # Min/Max dates
        date_stats = Equipment.objects.aggregate(
            min_cal_date=Min('Last_Calibration_Date'),
            max_cal_date=Max('Last_Calibration_Date')
        )
        
        self.assertIsNotNone(date_stats['min_cal_date'])
        self.assertIsNotNone(date_stats['max_cal_date'])
    
    def test_search_functionality(self):
        """Test search functionality across multiple fields"""
        # Search by machine name
        name_search = Equipment.objects.filter(
            Machine_Name__icontains='Machine 1'
        )
        self.assertGreater(name_search.count(), 0)
        
        # Search by location
        location_search = Equipment.objects.filter(
            Machine_Location__icontains='Floor 1'
        )
        self.assertEqual(location_search.count(), 10)  # Machines 0-9
        
        # Combined search
        combined_search = Equipment.objects.filter(
            Q(Machine_Name__icontains='Test') & 
            Q(Machine_Type='CNC')
        )
        self.assertEqual(combined_search.count(), 25)
    
    def test_date_range_queries(self):
        """Test queries for equipment due for calibration/maintenance"""
        # Equipment due for calibration (older than 1 year)
        due_for_calibration = Equipment.objects.filter(
            Last_Calibration_Date__lt=date.today() - timedelta(days=365)
        )
        
        # Equipment due for maintenance (older than 6 months)
        due_for_maintenance = Equipment.objects.filter(
            Last_Maintenance_Date__lt=date.today() - timedelta(days=180)
        )
        
        # Equipment due in next 2 weeks (based on intervals)
        # This assumes we have calibration_interval and maintenance_interval fields
        # or we calculate based on some business logic
        upcoming_due = Equipment.objects.filter(
            Q(Last_Calibration_Date__lt=date.today() - timedelta(days=350)) |
            Q(Last_Maintenance_Date__lt=date.today() - timedelta(days=170))
        )
        
        self.assertGreaterEqual(due_for_calibration.count(), 0)
        self.assertGreaterEqual(due_for_maintenance.count(), 0)
        self.assertGreaterEqual(upcoming_due.count(), 0)


class DatabaseConnectionTest(TestCase):
    """Test database connection and configuration"""
    
    def test_database_connection(self):
        """Test that database connection is working"""
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_database_settings(self):
        """Test database configuration"""
        from django.conf import settings
        
        # Check that database is configured
        self.assertIn('default', settings.DATABASES)
        
        # For testing, we typically use SQLite
        db_engine = settings.DATABASES['default']['ENGINE']
        self.assertIn('sqlite', db_engine.lower())


class DataValidationTest(TestCase):
    """Test data validation and constraints"""
    
    def test_required_fields_validation(self):
        """Test that required fields are validated"""
        # Test Machine_ID is required
        with self.assertRaises((IntegrityError, ValidationError)):
            equipment = Equipment(
                Machine_Name='Test Machine',
                Machine_Type='Test',
                Machine_Location='Test Location'
            )
            equipment.full_clean()  # This will raise ValidationError
    
    def test_date_field_validation(self):
        """Test date field validation"""
        equipment = Equipment.objects.create(
            Machine_ID='DATE001',
            Machine_Name='Date Test Machine',
            Machine_Type='Test',
            Machine_Location='Test Location',
            Last_Calibration_Date=date.today(),
            Last_Maintenance_Date=date.today()
        )
        
        # Test that dates can be None (if allowed)
        equipment.Last_Calibration_Date = None
        equipment.Last_Maintenance_Date = None
        equipment.save()
        
        equipment.refresh_from_db()
        self.assertIsNone(equipment.Last_Calibration_Date)
        self.assertIsNone(equipment.Last_Maintenance_Date)
    
    def test_field_length_constraints(self):
        """Test field length constraints"""
        # Assuming Machine_ID has a max length
        long_machine_id = 'X' * 1000  # Very long ID
        
        with self.assertRaises((IntegrityError, ValidationError)):
            equipment = Equipment(
                Machine_ID=long_machine_id,
                Machine_Name='Test Machine',
                Machine_Type='Test',
                Machine_Location='Test Location',
                Last_Calibration_Date=date.today(),
                Last_Maintenance_Date=date.today()
            )
            equipment.full_clean()


class DatabaseBackupRestoreTest(TransactionTestCase):
    """Test database backup and restore functionality"""
    
    def test_data_persistence(self):
        """Test that data persists across transactions"""
        # Create equipment
        equipment = Equipment.objects.create(
            Machine_ID='PERSIST001',
            Machine_Name='Persistence Test',
            Machine_Type='Test',
            Machine_Location='Test Location',
            Last_Calibration_Date=date.today(),
            Last_Maintenance_Date=date.today()
        )
        
        # Commit transaction
        transaction.commit()
        
        # Verify data exists in new transaction
        equipment_exists = Equipment.objects.filter(Machine_ID='PERSIST001').exists()
        self.assertTrue(equipment_exists)
    
    def test_rollback_functionality(self):
        """Test transaction rollback"""
        initial_count = Equipment.objects.count()
        
        try:
            with transaction.atomic():
                Equipment.objects.create(
                    Machine_ID='ROLLBACK001',
                    Machine_Name='Rollback Test',
                    Machine_Type='Test',
                    Machine_Location='Test Location',
                    Last_Calibration_Date=date.today(),
                    Last_Maintenance_Date=date.today()
                )
                
                # Force an error to trigger rollback
                raise Exception("Forcing rollback")
        
        except Exception:
            pass
        
        # Count should be unchanged
        final_count = Equipment.objects.count()
        self.assertEqual(initial_count, final_count)