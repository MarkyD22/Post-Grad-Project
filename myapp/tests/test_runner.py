import pytest
from django.test import Client
from django.contrib.auth.models import User
from myapp.models import UserProfile, Equipment  # Adjust import path
from datetime import date


@pytest.fixture
def client():
    """Provide a Django test client"""
    return Client()


@pytest.fixture
def admin_user(db):
    """Create an admin user for testing"""
    user = User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='TestPassword123!'
    )
    UserProfile.objects.create(
        user=user,
        role='Administrator',
        employee_id='ADM001'
    )
    return user


@pytest.fixture
def quality_user(db):
    """Create a quality user for testing"""
    user = User.objects.create_user(
        username='quality_test',
        email='quality@test.com',
        password='TestPassword123!'
    )
    UserProfile.objects.create(
        user=user,
        role='Quality',
        employee_id='QUA001'
    )
    return user


@pytest.fixture
def maintenance_user(db):
    """Create a maintenance user for testing"""
    user = User.objects.create_user(
        username='maintenance_test',
        email='maintenance@test.com',
        password='TestPassword123!'
    )
    UserProfile.objects.create(
        user=user,
        role='Maintenance',
        employee_id='MAI001'
    )
    return user


@pytest.fixture
def sample_equipment(db):
    """Create sample equipment for testing"""
    return Equipment.objects.create(
        Machine_ID='TEST001',
        Machine_Name='Test Machine',
        Machine_Type='Test Type',
        Machine_Location='Test Location',
        Last_Calibration_Date=date.today(),
        Last_Maintenance_Date=date.today()
    )


# tests/test_runner.py

import sys
import os
from django.test.runner import DiscoverRunner
from django.test.utils import get_runner
from django.conf import settings


class CustomTestRunner(DiscoverRunner):
    """Custom test runner with additional setup"""
    
    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        # Add any custom setup here
        print("Setting up test environment...")
    
    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        # Add any custom teardown here
        print("Tearing down test environment...")


def run_tests():
    """Function to run all tests"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings.test')
    
    import django
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # Run specific test modules
    test_modules = [
        'tests.test_models',
        'tests.test_auth',
        'tests.test_views',
        'tests.test_database',
    ]
    
    failures = test_runner.run_tests(test_modules)
    
    if failures:
        print(f"\n{failures} test(s) failed!")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == '__main__':
    run_tests()


# tests/settings.py - Test-specific settings

from S00044234_Maint_Calib_Db.settings import *  # Import base settings

# Override settings for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # Use in-memory database for faster tests
    }
}

# Disable migrations during testing for speed
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use dummy cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Use a simple password hasher for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Set test-specific email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Testing flags
TESTING = True
DEBUG = False


# tests/utils.py - Test utilities

from django.test import TestCase
from django.contrib.auth.models import User
from myapp.models import UserProfile, Equipment
from datetime import date, timedelta
import random
import string


class BaseTestCase(TestCase):
    """Base test case with common setup methods"""
    
    def create_user(self, username=None, role='Quality', **kwargs):
        """Helper method to create a user with profile"""
        if not username:
            username = f'testuser_{random.randint(1000, 9999)}'
        
        defaults = {
            'email': f'{username}@test.com',
            'password': 'TestPassword123!'
        }
        defaults.update(kwargs)
        
        user = User.objects.create_user(username=username, **defaults)
        UserProfile.objects.create(
            user=user,
            role=role,
            employee_id=f'{role[:3].upper()}{random.randint(100, 999)}'
        )
        return user
    
    def create_equipment(self, machine_id=None, **kwargs):
        """Helper method to create equipment"""
        if not machine_id:
            machine_id = f'EQ{random.randint(1000, 9999)}'
        
        defaults = {
            'Machine_Name': f'Test Machine {random.randint(1, 100)}',
            'Machine_Type': 'Test Type',
            'Machine_Location': 'Test Location',
            'Last_Calibration_Date': date.today() - timedelta(days=30),
            'Last_Maintenance_Date': date.today() - timedelta(days=15)
        }
        defaults.update(kwargs)
        
        return Equipment.objects.create(
            Machine_ID=machine_id,
            **defaults
        )
    
    def generate_random_string(self, length=10):
        """Generate a random string for testing"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class DatabaseTestMixin:
    """Mixin for database-related test utilities"""
    
    def assert_equipment_exists(self, machine_id):
        """Assert that equipment with given ID exists"""
        self.assertTrue(
            Equipment.objects.filter(Machine_ID=machine_id).exists(),
            f"Equipment with ID {machine_id} does not exist"
        )
    
    def assert_user_has_role(self, user, expected_role):
        """Assert that user has expected role"""
        self.assertEqual(
            user.userprofile.role,
            expected_role,
            f"Expected user to have role {expected_role}, got {user.userprofile.role}"
        )
    
    def assert_equipment_count(self, expected_count):
        """Assert the total number of equipment records"""
        actual_count = Equipment.objects.count()
        self.assertEqual(
            actual_count,
            expected_count,
            f"Expected {expected_count} equipment records, got {actual_count}"
        )


# Makefile for test commands

# test_commands.txt
"""
Commands to run tests:

# Run all tests
python manage.py test

# Run specific test module
python manage.py test tests.test_models

# Run specific test class
python manage.py test tests.test_models.EquipmentModelTest

# Run specific test method
python manage.py test tests.test_models.EquipmentModelTest.test_equipment_creation

# Run tests with verbose output
python manage.py test --verbosity=2

# Run tests with coverage (requires coverage.py)
coverage run --source='.' manage.py test
coverage report
coverage html

# Run tests in parallel (faster)
python manage.py test --parallel

# Run tests and keep test database
python manage.py test --keepdb

# Run tests with specific settings
python manage.py test --settings=tests.settings

# Using pytest (alternative)
pytest tests/
pytest tests/test_models.py
pytest tests/test_models.py::EquipmentModelTest::test_equipment_creation
pytest -v tests/  # verbose
pytest --cov=myapp tests/  # with coverage
"""