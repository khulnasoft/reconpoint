# Generated migration for adding performance indexes
# Based on DATABASE_MIGRATION_GUIDE.md recommendations

from django.db import migrations, models


class Migration(migrations.Migration):
    
    dependencies = [
        ('targetApp', '0001_initial'),
    ]

    operations = [
        # Domain indexes
        migrations.AddIndex(
            model_name='domain',
            index=models.Index(fields=['name'], name='domain_name_idx'),
        ),
        migrations.AddIndex(
            model_name='domain',
            index=models.Index(fields=['project', 'insert_date'], name='domain_project_date_idx'),
        ),
        migrations.AddIndex(
            model_name='domain',
            index=models.Index(fields=['start_scan_date'], name='domain_scan_date_idx'),
        ),
    ]
