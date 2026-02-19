from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinner', '0002_drop_legacy_final_option_column'),
    ]

    operations = [
        migrations.AddField(
            model_name='dinneroption',
            name='notes',
            field=models.TextField(blank=True),
        ),
    ]
