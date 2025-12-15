from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from myapp.models import UserProfile  # Adjust import path as needed


class UserCreationTest(TestCase):
    """Test cases for user creation and authentication"""
    
    def setUp(self):
        """Set up test client and data"""
        self.client = Client()
        self.signup_url = reverse('signup')  # Adjust URL name as needed
        self.login_url = reverse('login')    # Adjust URL name as needed
        
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
            'role': 'Quality',
            'employee_id': 'EMP001'
        }
    
    def test_user_signup_success(self):
        """Test successful user signup"""
        response = self.client.post(self.signup_url, self.user_data)
        
        # Check if user was created
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # Check if user profile was created
        user = User.objects.get(username='testuser')
        self.assertTrue(hasattr(user, 'userprofile'))
        self.assertEqual(user.userprofile.role, 'Quality')
        self.assertEqual(user.userprofile.employee_id, 'EMP001')
    
    def test_user_signup_password_mismatch(self):
        """Test signup with password mismatch"""
        data = self.user_data.copy()
        data['password2'] = 'DifferentPassword123!'
        
        response = self.client.post(self.signup_url, data)
        
        # User should not be created
        self.assertFalse(User.objects.filter(username='testuser').exists())
    
    def test_user_signup_duplicate_username(self):
        """Test signup with existing username"""
        # Create initial user
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='password123'
        )
        
        response = self.client.post(self.signup_url, self.user_data)
        
        # Should only have one user with this username
        self.assertEqual(User.objects.filter(username='testuser').count(), 1)
    
    def test_user_login_success(self):
        """Test successful user login"""
        # Create user first
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        UserProfile.objects.create(
            user=user,
            role='Quality',
            employee_id='EMP001'
        )
        
        login_data = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        # Check if user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        # Create user first
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        login_data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        # User should not be logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_user_authentication_method(self):
        """Test Django's authenticate method"""
        # Create user
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        # Test valid authentication
        user = authenticate(username='testuser', password='TestPassword123!')
        self.assertIsNotNone(user)
        
        # Test invalid authentication
        user = authenticate(username='testuser', password='WrongPassword')
        self.assertIsNone(user)
    
    def test_user_roles_assignment(self):
        """Test that users can be assigned different roles"""
        roles = ['Administrator', 'Maintenance', 'Quality']
        
        for i, role in enumerate(roles):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='TestPassword123!'
            )
            
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                employee_id=f'EMP00{i+1}'
            )
            
            self.assertEqual(profile.role, role)


class UserPermissionsTest(TestCase):
    """Test cases for user permissions and access control"""
    
    def setUp(self):
        """Set up test users with different roles"""
        self.client = Client()
        
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
    
    def test_admin_user_permissions(self):
        """Test that admin user has correct role"""
        self.assertEqual(self.admin_user.userprofile.role, 'Administrator')
    
    def test_quality_user_permissions(self):
        """Test that quality user has correct role"""
        self.assertEqual(self.quality_user.userprofile.role, 'Quality')
    
    def test_maintenance_user_permissions(self):
        """Test that maintenance user has correct role"""
        self.assertEqual(self.maintenance_user.userprofile.role, 'Maintenance')
    
    def test_user_can_access_dashboard_when_logged_in(self):
        """Test that logged in users can access dashboard"""
        self.client.login(username='quality', password='TestPassword123!')
        
        dashboard_url = reverse('dashboard')  # Adjust URL name as needed
        response = self.client.get(dashboard_url)
        
        # Should not redirect to login page
        self.assertNotEqual(response.status_code, 302)
    
    def test_anonymous_user_redirected_to_login(self):
        """Test that anonymous users are redirected to login"""
        dashboard_url = reverse('dashboard')  # Adjust URL name as needed
        response = self.client.get(dashboard_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)