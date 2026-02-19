from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('project', '0005_alter_customuser_profile_pic'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DinnerDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('dinner_eaten', models.CharField(blank=True, max_length=255)),
                ('decided_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('decided_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dinner_decisions', to=settings.AUTH_USER_MODEL)),
                ('family', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dinner_days', to='project.family')),
            ],
            options={
                'ordering': ['-date'],
                'constraints': [models.UniqueConstraint(fields=('family', 'date'), name='uniq_dinner_day_per_family_date')],
            },
        ),
        migrations.CreateModel(
            name='DinnerOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_dinner_options', to=settings.AUTH_USER_MODEL)),
                ('dinner_day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='dinner.dinnerday')),
            ],
            options={
                'ordering': ['created_at', 'id'],
                'constraints': [models.UniqueConstraint(fields=('dinner_day', 'name'), name='uniq_dinner_option_name_per_day')],
            },
        ),
        migrations.CreateModel(
            name='DinnerVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('dinner_day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='dinner.dinnerday')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='dinner.dinneroption')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dinner_votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'constraints': [models.UniqueConstraint(fields=('dinner_day', 'voter'), name='uniq_dinner_vote_per_day_per_user'), models.UniqueConstraint(fields=('option', 'voter'), name='uniq_dinner_vote_per_option_per_user')],
            },
        ),
    ]
