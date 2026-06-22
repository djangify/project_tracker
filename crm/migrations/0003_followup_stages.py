# Generated for crm app — follow-up stages & templates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0002_dashboard_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='follow_up_done',
        ),
        migrations.AddField(
            model_name='contact',
            name='follow_up_1_done',
            field=models.BooleanField(default=False, verbose_name='Follow-up 1 done'),
        ),
        migrations.AddField(
            model_name='contact',
            name='follow_up_2_done',
            field=models.BooleanField(default=False, verbose_name='Follow-up 2 done'),
        ),
        migrations.AddField(
            model_name='contact',
            name='follow_up_3_done',
            field=models.BooleanField(default=False, verbose_name='Follow-up 3 done'),
        ),
        migrations.CreateModel(
            name='FollowUpTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stage', models.PositiveSmallIntegerField(choices=[(1, 'Follow-up 1'), (2, 'Follow-up 2'), (3, 'Follow-up 3')], unique=True)),
                ('message', models.TextField(help_text='Reusable message for this follow-up stage')),
            ],
            options={
                'ordering': ['stage'],
            },
        ),
    ]
