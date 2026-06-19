# Generated migration for AuditLog model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clinic_queue', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create_token', 'Create Token'), ('call_next', 'Call Next'), ('complete_token', 'Complete Token'), ('cancel_token', 'Cancel Token'), ('update_settings', 'Update Settings'), ('archive_tokens', 'Archive Tokens')], max_length=20)),
                ('details', models.TextField(blank=True, help_text='JSON details of the action')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('token', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='clinic_queue.token')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action', '-created_at'], name='clinic_queu_action_created_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', '-created_at'], name='clinic_queu_user_id_created_idx'),
        ),
    ]
