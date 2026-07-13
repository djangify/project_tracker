# Rename joined_live_it_list -> joined_email_list (preserving data) and add project FK.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0003_followup_stages'),
        ('projects', '0006_backfill_task_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='joined_live_it_list',
            new_name='joined_email_list',
        ),
        migrations.AlterField(
            model_name='contact',
            name='joined_email_list',
            field=models.BooleanField(
                default=False,
                help_text='Signed up for the email list',
                verbose_name='Joined email list',
            ),
        ),
        migrations.AddField(
            model_name='contact',
            name='project',
            field=models.ForeignKey(
                blank=True,
                help_text='The business this contact relates to',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='contacts',
                to='projects.project',
            ),
        ),
    ]
