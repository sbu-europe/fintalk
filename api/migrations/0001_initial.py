# Generated migration for User model

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CardHolder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=100, unique=True)),
                ('phone_number', models.CharField(max_length=20, unique=True)),
                ('credit_card_number', models.CharField(max_length=19)),
                ('card_status', models.CharField(
                    choices=[('active', 'Active'), ('blocked', 'Blocked')],
                    default='active',
                    max_length=10
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'cardholders',
                'ordering': ['-created_at'],
            },
        ),
    ]
