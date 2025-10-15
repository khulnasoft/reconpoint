# Generated migration for adding performance indexes
# Based on DATABASE_MIGRATION_GUIDE.md recommendations

from django.db import migrations, models


class Migration(migrations.Migration):
    
    dependencies = [
        ('startScan', '0002_auto_20240911_0145'),
    ]

    operations = [
        # Subdomain indexes
        migrations.AddIndex(
            model_name='subdomain',
            index=models.Index(fields=['name'], name='subdomain_name_idx'),
        ),
        migrations.AddIndex(
            model_name='subdomain',
            index=models.Index(fields=['scan_history', 'name'], name='subdomain_scan_name_idx'),
        ),
        migrations.AddIndex(
            model_name='subdomain',
            index=models.Index(fields=['target_domain', 'discovered_date'], name='subdomain_domain_date_idx'),
        ),
        migrations.AddIndex(
            model_name='subdomain',
            index=models.Index(fields=['http_status'], name='subdomain_status_idx'),
        ),
        migrations.AddIndex(
            model_name='subdomain',
            index=models.Index(fields=['is_important'], name='subdomain_important_idx'),
        ),
        
        # Vulnerability indexes
        migrations.AddIndex(
            model_name='vulnerability',
            index=models.Index(fields=['scan_history', 'severity'], name='vuln_scan_severity_idx'),
        ),
        migrations.AddIndex(
            model_name='vulnerability',
            index=models.Index(fields=['target_domain', 'open_status'], name='vuln_domain_status_idx'),
        ),
        migrations.AddIndex(
            model_name='vulnerability',
            index=models.Index(fields=['discovered_date'], name='vuln_discovered_idx'),
        ),
        migrations.AddIndex(
            model_name='vulnerability',
            index=models.Index(fields=['severity'], name='vuln_severity_idx'),
        ),
        
        # EndPoint indexes
        migrations.AddIndex(
            model_name='endpoint',
            index=models.Index(fields=['scan_history', 'http_status'], name='endpoint_scan_status_idx'),
        ),
        migrations.AddIndex(
            model_name='endpoint',
            index=models.Index(fields=['subdomain'], name='endpoint_subdomain_idx'),
        ),
        migrations.AddIndex(
            model_name='endpoint',
            index=models.Index(fields=['http_url'], name='endpoint_url_idx'),
        ),
        
        # ScanHistory indexes
        migrations.AddIndex(
            model_name='scanhistory',
            index=models.Index(fields=['domain', 'start_scan_date'], name='scan_domain_date_idx'),
        ),
        migrations.AddIndex(
            model_name='scanhistory',
            index=models.Index(fields=['scan_status'], name='scan_status_idx'),
        ),
        migrations.AddIndex(
            model_name='scanhistory',
            index=models.Index(fields=['start_scan_date'], name='scan_start_date_idx'),
        ),
    ]
