"""
Comprehensive test suite for startScan module
"""

import pytest
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache

from .models import ScanHistory, Subdomain
from .services import (
    ScanStatisticsService,
    ScanQueryService,
    ScanValidationService,
    ScanCleanupService,
    ScanExportService
)
from .validators import (
    ScanInputValidator,
    SubdomainValidator,
    VulnerabilityValidator
)
from targetApp.models import Domain
from scanEngine.models import EngineType


class ScanHistoryModelTest(TestCase):
    """Tests for ScanHistory model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.domain = Domain.objects.create(
            name='example.com',
            description='Test domain'
        )
        
        self.scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
        
        self.scan = ScanHistory.objects.create(
            domain=self.domain,
            scan_type=self.scan_type,
            start_scan_date=timezone.now(),
            scan_status=1,  # Running
            initiated_by=self.user
        )
    
    def test_scan_creation(self):
        """Test scan creation"""
        self.assertIsNotNone(self.scan.id)
        self.assertEqual(self.scan.domain, self.domain)
        self.assertEqual(self.scan.scan_type, self.scan_type)
        self.assertEqual(self.scan.initiated_by, self.user)
    
    def test_scan_status_methods(self):
        """Test scan status check methods"""
        # Test running status
        self.scan.scan_status = 1
        self.assertTrue(self.scan.is_running())
        self.assertFalse(self.scan.is_completed())
        
        # Test completed status
        self.scan.scan_status = 2
        self.assertTrue(self.scan.is_completed())
        self.assertFalse(self.scan.is_running())
    
    def test_scan_duration(self):
        """Test scan duration calculation"""
        self.scan.stop_scan_date = self.scan.start_scan_date + timedelta(hours=2, minutes=30)
        duration = self.scan.get_scan_duration()
        
        self.assertIsNotNone(duration)
        self.assertEqual(duration, 9000)  # 2.5 hours in seconds
    
    def test_scan_duration_formatted(self):
        """Test formatted scan duration"""
        self.scan.stop_scan_date = self.scan.start_scan_date + timedelta(hours=1, minutes=30, seconds=45)
        formatted = self.scan.get_scan_duration_formatted()
        
        self.assertIn('1h', formatted)
        self.assertIn('30m', formatted)
        self.assertIn('45s', formatted)
    
    def test_get_subdomain_count(self):
        """Test subdomain count"""
        # Create test subdomains
        Subdomain.objects.create(
            scan_history=self.scan,
            target_domain=self.domain,
            name='sub1.example.com'
        )
        Subdomain.objects.create(
            scan_history=self.scan,
            target_domain=self.domain,
            name='sub2.example.com'
        )
        
        count = self.scan.get_subdomain_count()
        self.assertEqual(count, 2)
    
    def test_get_vulnerability_counts_optimized(self):
        """Test optimized vulnerability counts"""
        # This would require creating vulnerabilities
        # For now, test that it returns a dict
        counts = self.scan.get_vulnerability_counts_optimized()
        
        self.assertIsInstance(counts, dict)
        self.assertIn('total', counts)
        self.assertIn('critical', counts)
        self.assertIn('high', counts)
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()


class SubdomainModelTest(TestCase):
    """Tests for Subdomain model"""
    
    def setUp(self):
        """Set up test data"""
        self.domain = Domain.objects.create(name='example.com')
        self.subdomain = Subdomain.objects.create(
            target_domain=self.domain,
            name='test.example.com',
            http_status=200,
            http_url='https://test.example.com'
        )
    
    def test_subdomain_creation(self):
        """Test subdomain creation"""
        self.assertIsNotNone(self.subdomain.id)
        self.assertEqual(self.subdomain.name, 'test.example.com')
        self.assertEqual(self.subdomain.http_status, 200)
    
    def test_is_alive(self):
        """Test is_alive method"""
        # Test alive status codes
        for status in [200, 201, 301, 302]:
            self.subdomain.http_status = status
            self.assertTrue(self.subdomain.is_alive())
        
        # Test dead status codes
        for status in [0, 404, 500]:
            self.subdomain.http_status = status
            self.assertFalse(self.subdomain.is_alive())
    
    def test_get_risk_score(self):
        """Test risk score calculation"""
        score = self.subdomain.get_risk_score()
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_get_risk_level(self):
        """Test risk level determination"""
        level = self.subdomain.get_risk_level()
        self.assertIsInstance(level, str)
        self.assertIn('🔴', level or '🟢')  # Should contain an emoji


class ScanStatisticsServiceTest(TestCase):
    """Tests for ScanStatisticsService"""
    
    def setUp(self):
        """Set up test data"""
        self.domain = Domain.objects.create(name='example.com')
        self.scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
        self.scan = ScanHistory.objects.create(
            domain=self.domain,
            scan_type=self.scan_type,
            start_scan_date=timezone.now(),
            scan_status=2  # Completed
        )
    
    def test_get_scan_statistics(self):
        """Test getting scan statistics"""
        stats = ScanStatisticsService.get_scan_statistics(self.scan.id)
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['scan_id'], self.scan.id)
        self.assertIn('subdomains', stats)
        self.assertIn('endpoints', stats)
        self.assertIn('vulnerabilities', stats)
    
    def test_get_scan_statistics_caching(self):
        """Test statistics caching"""
        # First call - should cache
        stats1 = ScanStatisticsService.get_scan_statistics(self.scan.id, use_cache=True)
        
        # Second call - should use cache
        stats2 = ScanStatisticsService.get_scan_statistics(self.scan.id, use_cache=True)
        
        self.assertEqual(stats1, stats2)
    
    def test_invalidate_scan_cache(self):
        """Test cache invalidation"""
        # Get stats to populate cache
        ScanStatisticsService.get_scan_statistics(self.scan.id, use_cache=True)
        
        # Invalidate cache
        ScanStatisticsService.invalidate_scan_cache(self.scan.id)
        
        # Cache should be empty
        cache_key = f'scan_stats_{self.scan.id}'
        self.assertIsNone(cache.get(cache_key))
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()


class ScanValidationServiceTest(TestCase):
    """Tests for ScanValidationService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.domain = Domain.objects.create(name='example.com')
        self.scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
    
    def test_validate_scan_start_success(self):
        """Test successful scan start validation"""
        is_valid, error = ScanValidationService.validate_scan_start(
            self.domain.id,
            self.scan_type.id,
            self.user
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_scan_start_with_running_scan(self):
        """Test validation fails when scan is already running"""
        # Create a running scan
        ScanHistory.objects.create(
            domain=self.domain,
            scan_type=self.scan_type,
            start_scan_date=timezone.now(),
            scan_status=1  # Running
        )
        
        is_valid, error = ScanValidationService.validate_scan_start(
            self.domain.id,
            self.scan_type.id,
            self.user
        )
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn('already a running scan', error)
    
    def test_validate_scan_start_invalid_domain(self):
        """Test validation fails with invalid domain"""
        is_valid, error = ScanValidationService.validate_scan_start(
            99999,  # Non-existent domain
            self.scan_type.id,
            self.user
        )
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class ScanInputValidatorTest(TestCase):
    """Tests for ScanInputValidator"""
    
    def test_validate_scan_configuration_valid(self):
        """Test valid scan configuration"""
        config = {
            'out_of_scope_subdomains': ['test.example.com'],
            'imported_subdomains': ['sub.example.com'],
            'starting_point_path': 'https://example.com/start',
            'excluded_paths': ['/admin', '/api']
        }
        
        is_valid, error = ScanInputValidator.validate_scan_configuration(config)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_scan_configuration_invalid_subdomain(self):
        """Test invalid subdomain in configuration"""
        config = {
            'out_of_scope_subdomains': ['invalid..subdomain'],
        }
        
        is_valid, error = ScanInputValidator.validate_scan_configuration(config)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_subdomain_list(self):
        """Test subdomain list validation"""
        subdomains = ['valid.example.com', 'another.example.com']
        
        is_valid, error, valid_list = ScanInputValidator.validate_subdomain_list(subdomains)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertEqual(len(valid_list), 2)
    
    def test_validate_export_format_valid(self):
        """Test valid export format"""
        for format in ['json', 'csv', 'xml', 'pdf', 'html']:
            is_valid, error = ScanInputValidator.validate_export_format(format)
            self.assertTrue(is_valid)
            self.assertIsNone(error)
    
    def test_validate_export_format_invalid(self):
        """Test invalid export format"""
        is_valid, error = ScanInputValidator.validate_export_format('invalid')
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_sanitize_scan_name(self):
        """Test scan name sanitization"""
        name = "Test <script>alert('xss')</script> Scan"
        sanitized = ScanInputValidator.sanitize_scan_name(name)
        
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('</script>', sanitized)


class SubdomainValidatorTest(TestCase):
    """Tests for SubdomainValidator"""
    
    def test_validate_subdomain_data_valid(self):
        """Test valid subdomain data"""
        data = {
            'name': 'test.example.com',
            'http_url': 'https://test.example.com',
            'http_status': 200,
            'ip_addresses': ['192.168.1.1', '10.0.0.1']
        }
        
        is_valid, error = SubdomainValidator.validate_subdomain_data(data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_subdomain_data_invalid_name(self):
        """Test invalid subdomain name"""
        data = {
            'name': 'invalid..subdomain',
        }
        
        is_valid, error = SubdomainValidator.validate_subdomain_data(data)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_subdomain_data_invalid_ip(self):
        """Test invalid IP address"""
        data = {
            'name': 'test.example.com',
            'ip_addresses': ['999.999.999.999']
        }
        
        is_valid, error = SubdomainValidator.validate_subdomain_data(data)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)


class VulnerabilityValidatorTest(TestCase):
    """Tests for VulnerabilityValidator"""
    
    def test_validate_vulnerability_data_valid(self):
        """Test valid vulnerability data"""
        data = {
            'name': 'SQL Injection',
            'severity': 4,
            'url': 'https://example.com/vuln',
            'cve_ids': ['CVE-2021-12345'],
            'cwe_ids': ['CWE-89']
        }
        
        is_valid, error = VulnerabilityValidator.validate_vulnerability_data(data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_vulnerability_data_invalid_severity(self):
        """Test invalid severity"""
        data = {
            'name': 'Test Vulnerability',
            'severity': 10  # Invalid
        }
        
        is_valid, error = VulnerabilityValidator.validate_vulnerability_data(data)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_cve_format(self):
        """Test CVE format validation"""
        self.assertTrue(VulnerabilityValidator._validate_cve_format('CVE-2021-12345'))
        self.assertTrue(VulnerabilityValidator._validate_cve_format('CVE-2020-1234'))
        self.assertFalse(VulnerabilityValidator._validate_cve_format('CVE-123'))
        self.assertFalse(VulnerabilityValidator._validate_cve_format('INVALID'))
    
    def test_validate_cwe_format(self):
        """Test CWE format validation"""
        self.assertTrue(VulnerabilityValidator._validate_cwe_format('CWE-89'))
        self.assertTrue(VulnerabilityValidator._validate_cwe_format('CWE-123'))
        self.assertFalse(VulnerabilityValidator._validate_cwe_format('CWE'))
        self.assertFalse(VulnerabilityValidator._validate_cwe_format('INVALID'))


class ScanExportServiceTest(TestCase):
    """Tests for ScanExportService"""
    
    def setUp(self):
        """Set up test data"""
        self.domain = Domain.objects.create(name='example.com')
        self.scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
        self.scan = ScanHistory.objects.create(
            domain=self.domain,
            scan_type=self.scan_type,
            start_scan_date=timezone.now(),
            scan_status=2
        )
        
        # Create test subdomain
        self.subdomain = Subdomain.objects.create(
            scan_history=self.scan,
            target_domain=self.domain,
            name='test.example.com',
            http_status=200
        )
    
    def test_export_subdomains(self):
        """Test subdomain export"""
        export_data = ScanExportService.export_subdomains(self.scan.id, format='json')
        
        self.assertIsInstance(export_data, dict)
        self.assertEqual(export_data['scan_id'], self.scan.id)
        self.assertEqual(export_data['count'], 1)
        self.assertIn('data', export_data)
        self.assertEqual(len(export_data['data']), 1)


# Integration Tests

class ScanWorkflowIntegrationTest(TestCase):
    """Integration tests for complete scan workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.domain = Domain.objects.create(name='example.com')
        self.scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
    
    def test_complete_scan_workflow(self):
        """Test complete scan workflow from start to finish"""
        # 1. Validate scan can be started
        is_valid, error = ScanValidationService.validate_scan_start(
            self.domain.id,
            self.scan_type.id,
            self.user
        )
        self.assertTrue(is_valid)
        
        # 2. Create scan
        scan = ScanHistory.objects.create(
            domain=self.domain,
            scan_type=self.scan_type,
            start_scan_date=timezone.now(),
            scan_status=1,  # Running
            initiated_by=self.user
        )
        
        # 3. Add scan results
        subdomain = Subdomain.objects.create(
            scan_history=scan,
            target_domain=self.domain,
            name='test.example.com',
            http_status=200
        )
        
        # 4. Complete scan
        scan.scan_status = 2  # Completed
        scan.stop_scan_date = timezone.now()
        scan.save()
        
        # 5. Get statistics
        stats = ScanStatisticsService.get_scan_statistics(scan.id)
        self.assertEqual(stats['subdomains']['total'], 1)
        
        # 6. Export results
        export_data = ScanExportService.export_subdomains(scan.id)
        self.assertEqual(export_data['count'], 1)
        
        # 7. Clean up
        success, error = ScanCleanupService.delete_scan_data(scan.id, delete_files=False)
        self.assertTrue(success)


# Performance Tests

class ScanPerformanceTest(TestCase):
    """Performance tests for scan operations"""
    
    def setUp(self):
        """Set up test data"""
        self.domain = Domain.objects.create(name='example.com')
        self.scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
        self.scan = ScanHistory.objects.create(
            domain=self.domain,
            scan_type=self.scan_type,
            start_scan_date=timezone.now(),
            scan_status=2
        )
        
        # Create multiple subdomains
        for i in range(100):
            Subdomain.objects.create(
                scan_history=self.scan,
                target_domain=self.domain,
                name=f'sub{i}.example.com',
                http_status=200
            )
    
    def test_subdomain_count_performance(self):
        """Test subdomain count query performance"""
        import time
        
        start_time = time.time()
        count = self.scan.get_subdomain_count()
        end_time = time.time()
        
        self.assertEqual(count, 100)
        self.assertLess(end_time - start_time, 0.1)  # Should be fast
    
    def test_statistics_caching_performance(self):
        """Test statistics caching improves performance"""
        import time
        
        # First call - no cache
        start_time = time.time()
        stats1 = ScanStatisticsService.get_scan_statistics(self.scan.id, use_cache=False)
        first_call_time = time.time() - start_time
        
        # Second call - with cache
        start_time = time.time()
        stats2 = ScanStatisticsService.get_scan_statistics(self.scan.id, use_cache=True)
        cached_call_time = time.time() - start_time
        
        # Cached call should be significantly faster
        self.assertLess(cached_call_time, first_call_time)
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()


if __name__ == '__main__':
    pytest.main([__file__])
