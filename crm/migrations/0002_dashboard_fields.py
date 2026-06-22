# Generated for crm app — dashboard & image fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='joined_live_it_list',
            field=models.BooleanField(default=False, help_text='Signed up for the free Live It List'),
        ),
        migrations.AddField(
            model_name='contact',
            name='made_purchase',
            field=models.BooleanField(default=False, help_text='This contact has bought something'),
        ),
        migrations.AddField(
            model_name='contact',
            name='revenue',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Total amount this contact has paid', max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='interaction',
            name='image',
            field=models.ImageField(blank=True, help_text='Optional screenshot (e.g. of a comment or DM)', null=True, upload_to='crm/interactions/'),
        ),
    ]
