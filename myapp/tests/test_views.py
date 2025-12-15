from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date, timedelta
from myapp.models import Equipment, UserProfile  # Adjust import path as needed


class DashboardViewTest(TestCase):
    """Test cases for dashboard views based on user roles"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test equipment
        self.equipment1 = Equipment.objects.create(
            Machine_ID='EQ001',
            Machine_Name='CNC Machine Alpha',
            Machine_Type='CNC',
            Machine_Location='Factory Floor A',
            Last_Calibration_Date=date.today() - timedelta(days=350),  # Due soon
            Last_Maintenance_Date=date.today() - timedelta(days=10)
        )
        
        self.equipment2 = Equipment.objects.create(
            Machine_ID='EQ002',
            Machine_Name='Lathe Machine Beta',
            Machine_Type='Lathe',
            Machine_Location='Factory Floor B',
            Last_Calibration_Date=date.today() - timedelta(days=100),
            Last_Maintenance_Date=date.today() - timedelta(days=180)  # Due soon
        )
        
        # Create users with different roles
        self.admin_user = User.objects.create_user(
            username='admin',
            password='TestPassword123!'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role='Administrator',
            employee_id='ADM001'
        )
        
        self.quality_user = User.objects.create_user(
            username='quality',
            password='TestPassword123!'
        )
        UserProfile.objects.create(
            user=self.quality_user,
            role='Quality',
            employee_id='QUA001'
        )
        
        self.maintenance_user = User.objects.create_user(
            username='maintenance',
            password='TestPassword123!'
        )
        UserProfile.objects.create(
            user=self.maintenance_user,
            role='Maintenance',
            employee_id='MAI001'
        )
    
    def test_admin_dashboard_access(self):
        """Test that admin can access admin dashboard"""
        self.client.login(username='admin', password='TestPassword123!')
        
        response = self.client.get(reverse('admin_dashboard'))  # Adjust URL name
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Administrator Dashboard')
    
    def test_quality_dashboard_access(self):
        """Test that quality user can access quality dashboard"""
        self.client.login(username='quality', password='TestPassword123!')
        
        response = self.client.get(reverse('quality_dashboard'))  # Adjust URL name
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Quality Dashboard')
    
    def test_maintenance_dashboard_access(self):
        """Test that maintenance user can access maintenance dashboard"""
        self.client.login(username='maintenance', password='TestPassword123!')
        
        response = self.client.get(reverse('maintenance_dashboard'))  # Adjust URL name
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maintenance Dashboard')
    
    def test_role_based_access_control(self):
        """Test that users can only access their appropriate dashboards"""
        # Quality user trying to access admin dashboard
        self.client.login(username='quality', password='TestPassword123!')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Maintenance user trying to access quality dashboard
        self.client.login(username='maintenance', password='TestPassword123!')
        response = self.client.get(reverse('quality_dashboard'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_equipment_due_display_maintenance_user(self):
        """Test that maintenance user sees equipment due for maintenance"""
        self.client.login(username='maintenance', password='TestPassword123!')
        
        response = self.client.get(reverse('maintenance_dashboard'))
        
        # Should see equipment due for maintenance/calibration in next 2 weeks
        self.assertContains(response, 'EQ001')  # Due for calibration
        self.assertContains(response, 'EQ002')  # Due for maintenance
    
    def test_equipment_search_functionality(self):
        """Test equipment search functionality"""
        self.client.login(username='admin', password='TestPassword123!')
        
        # Test search by machine name
        response = self.client.get(reverse('equipment_search'), {'query': 'CNC'})
        self.assertContains(response, 'CNC Machine Alpha')
        self.assertNotContains(response, 'Lathe Machine Beta')
        
        # Test search by machine ID
        response = self.client.get(reverse('equipment_search'), {'query': 'EQ002'})
        self.assertContains(response, 'Lathe Machine Beta')
        self.assertNotContains(response, 'CNC Machine Alpha')
    
    def test_equipment_details_view(self):
        """Test equipment details view"""
        self.client.login(username='quality', password='TestPassword123!')
        
        response = self.client.get(
            reverse('equipment_detail', kwargs={'machine_id': 'EQ001'})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CNC Machine Alpha')
        self.assertContains(response, 'Factory Floor A')
    
    def test_homepage_not_logged_in(self):
        """Test homepage shows login/signup buttons when not logged in"""
        response = self.client.get(reverse('homepage'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'About')
    
    def test_homepage_logged_in_redirect(self):
        """Test homepage redirects to dashboard when logged in"""
        self.client.login(username='quality', password='TestPassword123!')
        
        response = self.client.get(reverse('homepage'))
        
        # Should redirect to appropriate dashboard
        self.assertEqual(response.status_code, 302)


class EquipmentManagementViewTest(TestCase):
    """Test cases for equipment management views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='TestPassword123!'
        )
        UserProfile.objects.create(
            user=self.admin_user,
            role='Administrator',
            employee_id='ADM001'
        )
        
        self.equipment_data = {
            'Machine_ID': 'EQ003',
            'Machine_Name': 'Test Machine',
            'Machine_Type': 'Testing',
            'Machine_Location': 'Test Floor',
            'Last_Calibration_Date': date.today().strftime('%Y-%m-%d'),
            'Last_Maintenance_Date': date.today().strftime('%Y-%m-%d')
        }
    
    def test_admin_can_add_equipment(self):
        """Test that admin can add new equipment"""
        self.client.login(username='admin', password='TestPassword123!')
        
        response = self.client.post(
            reverse('add_equipment'),
            self.equipment_data
        )
        
        # Check if equipment was created
        self.assertTrue(Equipment.objects.filter(Machine_ID='EQ003').exists())
    
    def test_admin_can_edit_equipment(self):
        """Test that admin can edit existing equipment"""
        equipment = Equipment.objects.create(
            Machine_ID='EQ004',
            Machine_Name='Original Name',
            Machine_Type='Original Type',
            Machine_Location='Original Location',
            Last_Calibration_Date=date.today(),
            Last_Maintenance_Date=date.today()
        )
        
        self.client.login(username='admin', password='TestPassword123!')
        
        updated_data = {
            'Machine_ID': 'EQ004',
            'Machine_Name': 'Updated Name',
            'Machine_Type': 'Updated Type',
            'Machine_Location': 'Updated Location',
            'Last_Calibration_Date': date.today().strftime('%Y-%m-%d'),
            'Last_Maintenance_Date': date.today().strftime('%Y-%m-%d')
        }
        
        response = self.client.post(
            reverse('edit_equipment', kwargs={'machine_id': 'EQ004'}),
            updated_data
        )
        
        equipment.refresh_from_db()
        self.assertEqual(equipment.Machine_Name, 'Updated Name')
    
    def test_admin_can_delete_equipment(self):
        """Test that admin can delete equipment"""
        equipment = Equipment.objects.create(
            Machine_ID='EQ005',
            Machine_Name='To Delete',
            Machine_Type='Test',
            Machine_Location='Test',
            Last_Calibration_Date=date.today(),
            Last_Maintenance_Date=date.today()
        )
        
        self.client.login(username='admin', password='TestPassword123!')
        
        response = self.client.post(
            reverse('delete_equipment', kwargs={'machine_id': 'EQ005'})
        )
        
        # Equipment should be deleted
        self.assertFalse(Equipment.objects.filter(Machine_ID='EQ005').exists())
    
    def test_non_admin_cannot_add_equipment(self):
        """Test that non-admin users cannot add equipment"""
        quality_user = User.objects.create_user(
            username='quality',
            password='TestPassword123!'
        )
        UserProfile.objects.create(
            user=quality_user,
            role='Quality',
            employee_id='QUA001'
        )
        
        self.client.login(username='quality', password='TestPassword123!')
        
        response = self.client.post(
            reverse('add_equipment'),
            self.equipment_data
        )
        
        # Should be forbidden
        self.assertEqual(response.status_code, 403)
    
    def test_maintenance_user_can_update_dates(self):
        """Test that maintenance user can update calibration and maintenance dates"""
        equipment = Equipment.objects.create(
            Machine_ID='EQ006',
            Machine_Name='Test Machine',
            Machine_Type='Test',
            Machine_Location='Test',
            Last_Calibration_Date=date.today() - timedelta(days=30),
            Last_Maintenance_Date=date.today() - timedelta(days=15)
        )
        
        maintenance_user = User.objects.create_user(
            username='maintenance',
            password='TestPassword123!'
        )
        UserProfile.objects.create(
            user=maintenance_user,
            role='Maintenance',
            employee_id='MAI001'
        )
        
        self.client.login(username='maintenance', password='TestPassword123!')
        
        new_date = date.today().strftime('%Y-%m-%d')
        response = self.client.post(
            reverse('update_equipment_dates', kwargs={'machine_id': 'EQ006'}),
            {
                'Last_Calibration_Date': new_date,
                'Last_Maintenance_Date': new_date
            }
        )
        
        equipment.refresh_from_db()
        self.assertEqual(equipment.Last_Calibration_Date, date.today())
        self.assertEqual(equipment.Last_Maintenance_Date, date.today())