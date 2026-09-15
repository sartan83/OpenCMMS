from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='AuditEntry',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('event_id', models.CharField(max_length=64, unique=True)),
                ('actor_id', models.IntegerField()),
                ('actor_username', models.CharField(max_length=150)),
                ('action', models.CharField(max_length=50)),
                ('entity_type', models.CharField(max_length=100)),
                ('entity_id', models.IntegerField()),
                ('entity_repr', models.CharField(blank=True, max_length=255)),
                ('diff', models.JSONField(default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('service', models.CharField(max_length=100)),
                ('occurred_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-occurred_at', '-created_at']},
        ),
    ]
