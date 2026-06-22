# Generated for crm app

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('platform', models.CharField(choices=[('instagram', 'Instagram'), ('linkedin', 'LinkedIn'), ('x', 'X / Twitter'), ('facebook', 'Facebook'), ('tiktok', 'TikTok'), ('youtube', 'YouTube'), ('threads', 'Threads'), ('reddit', 'Reddit'), ('email', 'Email'), ('referral', 'Referral'), ('other', 'Other')], default='instagram', help_text='Where you found them', max_length=20)),
                ('social_handle', models.CharField(blank=True, help_text='Their @username on that platform', max_length=150)),
                ('profile_url', models.URLField(blank=True, help_text='Link to their profile')),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('status', models.CharField(choices=[('new', 'New'), ('contacted', 'Contacted'), ('replied', 'Replied'), ('in_conversation', 'In conversation'), ('converted', 'Converted'), ('dead', 'Dead / No interest')], default='new', max_length=20)),
                ('tags', models.CharField(blank=True, help_text='Comma-separated, e.g. coach, warm lead', max_length=255)),
                ('notes', models.TextField(blank=True)),
                ('follow_up_date', models.DateField(blank=True, help_text='When to follow up next', null=True)),
                ('follow_up_done', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Interaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.localdate)),
                ('channel', models.CharField(choices=[('dm', 'Direct message'), ('comment', 'Comment'), ('email', 'Email'), ('call', 'Call'), ('meeting', 'Meeting'), ('other', 'Other')], default='dm', max_length=20)),
                ('direction', models.CharField(choices=[('outbound', 'I reached out'), ('inbound', 'They reached out')], default='outbound', max_length=20)),
                ('message', models.TextField(help_text='What was said')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='interactions', to='crm.contact')),
            ],
            options={
                'ordering': ['-date', '-created_at'],
            },
        ),
    ]
