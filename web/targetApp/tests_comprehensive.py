"""
Comprehensive test suite for targetApp module
"""

import pytest
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.cache import cache

from .models import Domain, Organization, DomainInfo, Registrar
from .services import (
    DomainService,
    OrganizationService,
    DomainInfoService,
    TargetImportService
)
from .validators import (
    TargetValidator,
    OrganizationValidator,
    FileUploadValidator,
    TargetInputParser
)
from dashboard.models import Project


class DomainModelTest(TestCase):
    """Tests for Domain model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project'
        )
        
        self.domain = Domain.objects.create(
            name='example.com',
            description='Test domain',
            project=self.project,
            insert_date=timezone.now()
        )
    
    def test_domain_creation(self):
        """Test domain creation"""
        self.assertIsNotNone(self.domain.id)
        self.assertEqual(self.domain.name, 'example.com')
        self.assertEqual(self.domain.project, self.project)
    
    def test_get_scan_count(self):
        """Test scan count method"""
        from startScan.models import ScanHistory
        from scanEngine.models import EngineType
        
        # Create scan type
        scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
        
        # Create scans
        for i in range(3):
            ScanHistory.objects.create(
                domain=self.domain,
                scan_type=scan_type,
                start_scan_date=timezone.now(),
                scan_status=2
            )
        
        count = self.domain.get_scan_count()
        self.assertEqual(count, 3)
    
    def test_has_running_scan(self):
        """Test running scan check"""
        from startScan.models import ScanHistory
        from scanEngine.models import EngineType
        
        scan_type = EngineType.objects.create(
            engine_name='Test Engine',
            yaml_configuration='{}'
        )
        
        # No running scan
        self.assertFalse(self.domain.has_running_scan())
        
        # Create running scan
        ScanHistory.objects.create(
            domain=self.domain,
            scan_type=scan_type,
            start_scan_date=timezone.now(),
            scan_status=1  # Running
        )
        
        self.assertTrue(self.domain.has_running_scan())
    
    def test_get_risk_score(self):
        """Test risk score calculation"""
        score = self.domain.get_risk_score()
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
    
    def test_get_risk_level(self):
        """Test risk level determination"""
        level = self.domain.get_risk_level()
        self.assertIsInstance(level, str)
        self.assertIn('🔴', level or '⚪')  # Should contain an emoji
    
    def test_get_domain_summary(self):
        """Test domain summary"""
        summary = self.domain.get_domain_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['name'], 'example.com')
        self.assertIn('scan_count', summary)
        self.assertIn('vulnerability_count', summary)
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()


class OrganizationModelTest(TestCase):
    """Tests for Organization model"""
    
    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project'
        )
        
        self.organization = Organization.objects.create(
            name='Test Organization',
            description='Test description',
            project=self.project,
            insert_date=timezone.now()
        )
        
        # Create test domains
        self.domain1 = Domain.objects.create(
            name='domain1.com',
            project=self.project,
            insert_date=timezone.now()
        )
        self.domain2 = Domain.objects.create(
            name='domain2.com',
            project=self.project,
            insert_date=timezone.now()
        )
        
        self.organization.domains.add(self.domain1, self.domain2)
    
    def test_organization_creation(self):
        """Test organization creation"""
        self.assertIsNotNone(self.organization.id)
        self.assertEqual(self.organization.name, 'Test Organization')
        self.assertEqual(self.organization.project, self.project)
    
    def test_get_domain_count(self):
        """Test domain count"""
        count = self.organization.get_domain_count()
        self.assertEqual(count, 2)
    
    def test_get_domains(self):
        """Test get domains method"""
        domains = self.organization.get_domains()
        self.assertEqual(domains.count(), 2)
    
    def test_get_organization_summary(self):
        """Test organization summary"""
        summary = self.organization.get_organization_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary['name'], 'Test Organization')
        self.assertEqual(summary['domain_count'], 2)


class DomainServiceTest(TestCase):
    """Tests for DomainService"""
    
    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project'
        )
    
    def test_create_domain(self):
        """Test domain creation via service"""
        domain, created = DomainService.create_domain(
            name='test.com',
            project=self.project,
            description='Test domain'
        )
        
        self.assertTrue(created)
        self.assertEqual(domain.name, 'test.com')
        self.assertEqual(domain.project, self.project)
    
    def test_create_duplicate_domain(self):
        """Test creating duplicate domain"""
        # Create first domain
        domain1, created1 = DomainService.create_domain(
            name='test.com',
            project=self.project
        )
        self.assertTrue(created1)
        
        # Try to create duplicate
        domain2, created2 = DomainService.create_domain(
            name='test.com',
            project=self.project
        )
        self.assertFalse(created2)
        self.assertEqual(domain1.id, domain2.id)
    
    def test_get_domain_statistics(self):
        """Test getting domain statistics"""
        domain = Domain.objects.create(
            name='test.com',
            project=self.project,
            insert_date=timezone.now()
        )
        
        stats = DomainService.get_domain_statistics(domain.id)
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['domain_id'], domain.id)
        self.assertIn('scans', stats)
        self.assertIn('subdomains', stats)
        self.assertIn('vulnerabilities', stats)
    
    def test_delete_domain(self):
        """Test domain deletion"""
        domain = Domain.objects.create(
            name='test.com',
            project=self.project,
            insert_date=timezone.now()
        )
        domain_id = domain.id
        
        success, error = DomainService.delete_domain(domain_id, delete_scan_results=False)
        
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertFalse(Domain.objects.filter(id=domain_id).exists())
    
    def test_bulk_delete_domains(self):
        """Test bulk domain deletion"""
        # Create multiple domains
        domain_ids = []
        for i in range(3):
            domain = Domain.objects.create(
                name=f'test{i}.com',
                project=self.project,
                insert_date=timezone.now()
            )
            domain_ids.append(domain.id)
        
        deleted_count, errors = DomainService.bulk_delete_domains(domain_ids)
        
        self.assertEqual(deleted_count, 3)
        self.assertEqual(len(errors), 0)
        self.assertEqual(Domain.objects.filter(id__in=domain_ids).count(), 0)
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()


class OrganizationServiceTest(TestCase):
    """Tests for OrganizationService"""
    
    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project'
        )
        
        self.domain = Domain.objects.create(
            name='test.com',
            project=self.project,
            insert_date=timezone.now()
        )
    
    def test_create_organization(self):
        """Test organization creation"""
        org, created = OrganizationService.create_organization(
            name='Test Org',
            project=self.project,
            description='Test description',
            domain_ids=[self.domain.id]
        )
        
        self.assertTrue(created)
        self.assertEqual(org.name, 'Test Org')
        self.assertEqual(org.domains.count(), 1)
    
    def test_get_organization_statistics(self):
        """Test organization statistics"""
        org = Organization.objects.create(
            name='Test Org',
            project=self.project,
            insert_date=timezone.now()
        )
        org.domains.add(self.domain)
        
        stats = OrganizationService.get_organization_statistics(org.id)
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['organization_id'], org.id)
        self.assertEqual(stats['domain_count'], 1)
    
    def test_update_organization_domains(self):
        """Test updating organization domains"""
        org = Organization.objects.create(
            name='Test Org',
            project=self.project,
            insert_date=timezone.now()
        )
        
        # Create new domain
        domain2 = Domain.objects.create(
            name='test2.com',
            project=self.project,
            insert_date=timezone.now()
        )
        
        success, error = OrganizationService.update_organization_domains(
            org.id,
            [self.domain.id, domain2.id]
        )
        
        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertEqual(org.domains.count(), 2)


class TargetValidatorTest(TestCase):
    """Tests for TargetValidator"""
    
    def test_validate_domain(self):
        """Test domain validation"""
        is_valid, error, classification = TargetValidator.validate_target_input('example.com')
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertTrue(classification['is_domain'])
    
    def test_validate_ip(self):
        """Test IP validation"""
        is_valid, error, classification = TargetValidator.validate_target_input('192.168.1.1')
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertTrue(classification['is_ip'])
    
    def test_validate_url(self):
        """Test URL validation"""
        is_valid, error, classification = TargetValidator.validate_target_input('https://example.com')
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertTrue(classification['is_url'])
    
    def test_validate_cidr(self):
        """Test CIDR validation"""
        is_valid, error, classification = TargetValidator.validate_target_input('192.168.1.0/24')
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        self.assertTrue(classification['is_cidr'])
    
    def test_validate_invalid_target(self):
        """Test invalid target"""
        is_valid, error, classification = TargetValidator.validate_target_input('invalid..domain')
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_bulk_targets(self):
        """Test bulk target validation"""
        targets = ['example.com', '192.168.1.1', 'invalid..domain']
        valid, invalid = TargetValidator.validate_bulk_targets(targets)
        
        self.assertEqual(len(valid), 2)
        self.assertEqual(len(invalid), 1)
    
    def test_validate_domain_name(self):
        """Test domain name validation"""
        is_valid, error = TargetValidator.validate_domain_name('example.com')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        is_valid, error = TargetValidator.validate_domain_name('invalid..domain')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_h1_team_handle(self):
        """Test HackerOne team handle validation"""
        is_valid, error = TargetValidator.validate_h1_team_handle('valid_handle')
        self.assertTrue(is_valid)
        
        is_valid, error = TargetValidator.validate_h1_team_handle('invalid handle!')
        self.assertFalse(is_valid)


class OrganizationValidatorTest(TestCase):
    """Tests for OrganizationValidator"""
    
    def test_validate_organization_name(self):
        """Test organization name validation"""
        is_valid, error = OrganizationValidator.validate_organization_name('Valid Organization')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        is_valid, error = OrganizationValidator.validate_organization_name('')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_validate_organization_description(self):
        """Test organization description validation"""
        is_valid, error = OrganizationValidator.validate_organization_description('Valid description')
        self.assertTrue(is_valid)
        
        # Test too long description
        long_desc = 'x' * 1001
        is_valid, error = OrganizationValidator.validate_organization_description(long_desc)
        self.assertFalse(is_valid)


class TargetInputParserTest(TestCase):
    """Tests for TargetInputParser"""
    
    def test_parse_domain(self):
        """Test parsing domain"""
        result = TargetInputParser.parse_target('example.com')
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['type'], 'domain')
        self.assertIn('example.com', result['domains'])
    
    def test_parse_url(self):
        """Test parsing URL"""
        result = TargetInputParser.parse_target('https://example.com:8080/path')
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['type'], 'url')
        self.assertIn('https://example.com:8080/path', result['urls'])
        self.assertIn(8080, result['ports'])
    
    def test_parse_ip(self):
        """Test parsing IP"""
        result = TargetInputParser.parse_target('192.168.1.1')
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['type'], 'ip')
        self.assertIn('192.168.1.1', result['ips'])
    
    def test_parse_cidr(self):
        """Test parsing CIDR"""
        result = TargetInputParser.parse_target('192.168.1.0/24')
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['type'], 'cidr')
        self.assertEqual(result['cidr'], '192.168.1.0/24')
    
    def test_parse_bulk_targets(self):
        """Test parsing multiple targets"""
        targets = ['example.com', 'https://test.com', '192.168.1.1', 'invalid..domain']
        result = TargetInputParser.parse_bulk_targets(targets)
        
        self.assertEqual(result['summary']['total'], 4)
        self.assertEqual(result['summary']['valid'], 3)
        self.assertEqual(result['summary']['invalid'], 1)


class TargetImportServiceTest(TestCase):
    """Tests for TargetImportService"""
    
    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project'
        )
    
    def test_import_from_text(self):
        """Test importing from text"""
        text_content = "example.com\ntest.com\nsample.com"
        
        imported_count, errors = TargetImportService.import_from_text(
            text_content,
            self.project,
            description='Imported targets'
        )
        
        self.assertEqual(imported_count, 3)
        self.assertEqual(len(errors), 0)
        self.assertEqual(Domain.objects.count(), 3)
    
    def test_import_from_csv(self):
        """Test importing from CSV"""
        csv_content = "example.com,Description 1,Org 1\ntest.com,Description 2,Org 2"
        
        imported_count, errors = TargetImportService.import_from_csv(
            csv_content,
            self.project
        )
        
        self.assertEqual(imported_count, 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(Domain.objects.count(), 2)
        self.assertEqual(Organization.objects.count(), 2)


class DomainIntegrationTest(TestCase):
    """Integration tests for domain operations"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project'
        )
    
    def test_complete_domain_workflow(self):
        """Test complete domain workflow"""
        # 1. Create domain
        domain, created = DomainService.create_domain(
            name='example.com',
            project=self.project,
            description='Test domain'
        )
        self.assertTrue(created)
        
        # 2. Get statistics
        stats = DomainService.get_domain_statistics(domain.id)
        self.assertEqual(stats['domain_name'], 'example.com')
        
        # 3. Get summary
        summary = domain.get_domain_summary()
        self.assertIsInstance(summary, dict)
        
        # 4. Delete domain
        success, error = DomainService.delete_domain(domain.id, delete_scan_results=False)
        self.assertTrue(success)


class DomainManagerTest(TestCase):
    """Tests for custom Domain manager"""
    
    def setUp(self):
        """Set up test data"""
        self.project = Project.objects.create(
            name='Test Project',
            slug='test-project'
        )
        
        # Create test domains
        for i in range(5):
            Domain.objects.create(
                name=f'test{i}.com',
                project=self.project,
                insert_date=timezone.now()
            )
    
    def test_recent_domains(self):
        """Test recent domains query"""
        recent = Domain.objects.recent(days=7)
        self.assertEqual(recent.count(), 5)
    
    def test_optimized_list(self):
        """Test optimized list query"""
        domains = Domain.objects.optimized_list()
        self.assertEqual(domains.count(), 5)


if __name__ == '__main__':
    pytest.main([__file__])
