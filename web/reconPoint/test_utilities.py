"""
Testing utilities for reconPoint.
"""
import json
from typing import Dict, Any, Optional, List
from unittest.mock import Mock, patch

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from targetApp.models import Domain, Organization
from scanEngine.models import EngineType
from startScan.models import ScanHistory, Subdomain, EndPoint, Vulnerability


class ReconPointTestCase(TestCase):
    """Base test case for reconPoint with common setup."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test organization
        self.organization = Organization.objects.create(
            name='Test Organization',
            description='Test organization for unit tests'
        )
        
        # Create test domain
        self.domain = Domain.objects.create(
            name='example.com',
            description='Test domain'
        )
        
        # Create test engine
        self.engine = EngineType.objects.create(
            engine_name='test_engine',
            yaml_configuration=self.get_test_engine_config()
        )
    
    def get_test_engine_config(self) -> str:
        """Get test engine YAML configuration."""
        return """
        subdomain_discovery: true
        port_scan: true
        vulnerability_scan: false
        """
    
    def create_test_scan(self, domain: Optional[Domain] = None) -> ScanHistory:
        """
        Create a test scan history.
        
        Args:
            domain: Domain to scan (uses self.domain if not provided)
            
        Returns:
            ScanHistory instance
        """
        if domain is None:
            domain = self.domain
        
        return ScanHistory.objects.create(
            domain=domain,
            scan_type=self.engine,
            initiated_by=self.user,
            scan_status=2  # Success
        )
    
    def create_test_subdomain(
        self,
        name: str = 'test.example.com',
        scan: Optional[ScanHistory] = None
    ) -> Subdomain:
        """
        Create a test subdomain.
        
        Args:
            name: Subdomain name
            scan: ScanHistory instance
            
        Returns:
            Subdomain instance
        """
        if scan is None:
            scan = self.create_test_scan()
        
        return Subdomain.objects.create(
            name=name,
            scan_history=scan,
            target_domain=self.domain
        )
    
    def create_test_endpoint(
        self,
        url: str = 'https://example.com/test',
        scan: Optional[ScanHistory] = None
    ) -> EndPoint:
        """
        Create a test endpoint.
        
        Args:
            url: Endpoint URL
            scan: ScanHistory instance
            
        Returns:
            EndPoint instance
        """
        if scan is None:
            scan = self.create_test_scan()
        
        return EndPoint.objects.create(
            url=url,
            scan_history=scan,
            http_status=200
        )
    
    def create_test_vulnerability(
        self,
        name: str = 'Test Vulnerability',
        scan: Optional[ScanHistory] = None
    ) -> Vulnerability:
        """
        Create a test vulnerability.
        
        Args:
            name: Vulnerability name
            scan: ScanHistory instance
            
        Returns:
            Vulnerability instance
        """
        if scan is None:
            scan = self.create_test_scan()
        
        return Vulnerability.objects.create(
            name=name,
            scan_history=scan,
            severity=3  # High
        )


class ReconPointAPITestCase(APITestCase, ReconPointTestCase):
    """Base API test case for reconPoint."""
    
    def setUp(self):
        """Set up API test fixtures."""
        super().setUp()
        
        # Create API client
        self.client = APIClient()
        
        # Authenticate client
        self.client.force_authenticate(user=self.user)
    
    def assert_response_status(self, response, expected_status: int):
        """
        Assert response status code.
        
        Args:
            response: Response object
            expected_status: Expected status code
        """
        self.assertEqual(
            response.status_code,
            expected_status,
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.data if hasattr(response, 'data') else response.content}"
        )
    
    def assert_response_contains_keys(self, response, keys: List[str]):
        """
        Assert response contains specific keys.
        
        Args:
            response: Response object
            keys: List of expected keys
        """
        response_data = response.json() if hasattr(response, 'json') else response.data
        
        for key in keys:
            self.assertIn(
                key,
                response_data,
                f"Expected key '{key}' not found in response"
            )
    
    def assert_validation_error(self, response, field: Optional[str] = None):
        """
        Assert response is a validation error.
        
        Args:
            response: Response object
            field: Optional field name that should have error
        """
        self.assert_response_status(response, status.HTTP_400_BAD_REQUEST)
        
        if field:
            response_data = response.json() if hasattr(response, 'json') else response.data
            self.assertIn(field, response_data)
    
    def get_json_response(self, response) -> Dict[str, Any]:
        """
        Get JSON response data.
        
        Args:
            response: Response object
            
        Returns:
            Response data as dictionary
        """
        if hasattr(response, 'json'):
            return response.json()
        elif hasattr(response, 'data'):
            return response.data
        else:
            return json.loads(response.content)


class CeleryTaskTestCase(TransactionTestCase):
    """Base test case for Celery tasks."""
    
    def setUp(self):
        """Set up Celery task test fixtures."""
        super().setUp()
        
        # Mock Celery task execution
        self.celery_patcher = patch('celery.app.task.Task.apply_async')
        self.mock_apply_async = self.celery_patcher.start()
        self.mock_apply_async.return_value = Mock(id='test-task-id')
    
    def tearDown(self):
        """Clean up after tests."""
        self.celery_patcher.stop()
        super().tearDown()
    
    def assert_task_called(self, task_name: str, times: int = 1):
        """
        Assert Celery task was called.
        
        Args:
            task_name: Name of the task
            times: Expected number of calls
        """
        call_count = sum(
            1 for call in self.mock_apply_async.call_args_list
            if task_name in str(call)
        )
        
        self.assertEqual(
            call_count,
            times,
            f"Expected task '{task_name}' to be called {times} time(s), "
            f"but was called {call_count} time(s)"
        )


class MockExternalService:
    """Mock external service responses for testing."""
    
    @staticmethod
    def mock_successful_response(data: Dict[str, Any], status_code: int = 200):
        """
        Create a mock successful response.
        
        Args:
            data: Response data
            status_code: HTTP status code
            
        Returns:
            Mock response object
        """
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data
        mock_response.text = json.dumps(data)
        mock_response.ok = True
        return mock_response
    
    @staticmethod
    def mock_error_response(status_code: int = 500, error_message: str = 'Internal Server Error'):
        """
        Create a mock error response.
        
        Args:
            status_code: HTTP status code
            error_message: Error message
            
        Returns:
            Mock response object
        """
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {'error': error_message}
        mock_response.text = error_message
        mock_response.ok = False
        return mock_response


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_scan_data(
        domain_name: str = 'example.com',
        engine_name: str = 'test_engine',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create test scan data.
        
        Args:
            domain_name: Domain name
            engine_name: Engine name
            **kwargs: Additional scan data
            
        Returns:
            Dictionary with scan data
        """
        data = {
            'domain': domain_name,
            'engine': engine_name,
            'scan_type': 'live'
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_subdomain_data(
        name: str = 'test.example.com',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create test subdomain data.
        
        Args:
            name: Subdomain name
            **kwargs: Additional subdomain data
            
        Returns:
            Dictionary with subdomain data
        """
        data = {
            'name': name,
            'http_status': 200,
            'is_important': False
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_vulnerability_data(
        name: str = 'Test Vulnerability',
        severity: str = 'high',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create test vulnerability data.
        
        Args:
            name: Vulnerability name
            severity: Severity level
            **kwargs: Additional vulnerability data
            
        Returns:
            Dictionary with vulnerability data
        """
        data = {
            'name': name,
            'severity': severity,
            'description': 'Test vulnerability description'
        }
        data.update(kwargs)
        return data


def create_test_user(
    username: str = 'testuser',
    email: str = 'test@example.com',
    password: str = 'testpass123',
    is_superuser: bool = False
) -> User:
    """
    Create a test user.
    
    Args:
        username: Username
        email: Email address
        password: Password
        is_superuser: Whether user is superuser
        
    Returns:
        User instance
    """
    if is_superuser:
        return User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
    else:
        return User.objects.create_user(
            username=username,
            email=email,
            password=password
        )


def assert_model_fields(test_case: TestCase, instance, expected_fields: Dict[str, Any]):
    """
    Assert model instance has expected field values.
    
    Args:
        test_case: TestCase instance
        instance: Model instance
        expected_fields: Dictionary of field names and expected values
    """
    for field, expected_value in expected_fields.items():
        actual_value = getattr(instance, field)
        test_case.assertEqual(
            actual_value,
            expected_value,
            f"Field '{field}' expected to be {expected_value}, got {actual_value}"
        )


def mock_celery_task(task_func):
    """
    Decorator to mock Celery task execution.
    
    Args:
        task_func: Task function to mock
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        # Execute task synchronously for testing
        return task_func(*args, **kwargs)
    
    return wrapper
